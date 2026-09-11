"""Render one native command plan. No execution, scheduler, credentials or GPU access."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex

from native_config import MODEL, aris_argv, validate_brief

SYSTEMS = ('ai-scientist-v1', 'ai-scientist-v2', 'arbor', 'aris-code')


def build(ledger, system, brief):
    if system not in SYSTEMS:
        raise ValueError('exactly one supported system required')
    validate_brief(brief)
    settings = ledger['approved_settings']
    selected = settings[system]
    policy = settings['launch_selection']
    if (policy['mode'] != 'user_selected_single_system' or policy['fixed_order'] is not None
            or policy['max_active_runs'] != 1 or policy['auto_start_next'] is not False):
        raise ValueError('manual single-run policy required')
    if system == 'ai-scientist-v1':
        argv = ['/env/bin/python', '/engine/launch_scientist.py', '--experiment', 'autoresearch',
                '--model', MODEL, '--num-ideas', str(selected['num_ideas']), '--parallel',
                str(selected['parallel']), '--gpus', '0', '--writeup', 'latex',
                '--engine', 'semanticscholar']
        if selected['improvement']:
            argv.append('--improvement')
        commands = [argv]
        staging = ['Stage native templates/autoresearch in writable project workspace.',
                   'Verify native MAX_RUNS/MAX_ITERS/NUM_REFLECTIONS against approved values.']
    elif system == 'ai-scientist-v2':
        commands = [
            ['/env/bin/python', '/engine/ai_scientist/perform_ideation_temp_free.py',
             '--model', MODEL, '--max-num-generations', str(selected['max_num_generations']),
             '--num-reflections', str(selected['idea_generation_and_reflection_total_rounds']),
             '--workshop-file', '/work/project/brief.md'],
            ['/env/bin/python', '/engine/launch_scientist_bfts.py', '--load_ideas',
             '/work/project/brief.json', '--writeup-type', 'normal', '--idea_idx', '0',
             '--attempt_id', '0', '--writeup-retries', str(selected['writeup_max_attempts']),
             '--num_cite_rounds', str(selected['num_cite_rounds'])]]
        for role in ('agg_plots', 'writeup', 'citation', 'writeup_small', 'review'):
            commands[1] += ['--model_'+role, MODEL]
        staging = ['Copy frozen brief byte-for-byte to writable brief.md.',
                   'Verify BFTS config and writeup defaults against all approved values.',
                   'Second command is the same system; proceed only after successful ideation.']
    elif system == 'arbor':
        commands = [['/env/bin/python', '-m', 'arbor.run', '--cwd', '/work/project',
                     '--config', '/work/project/research_config.yaml', '--run-name', 'run',
                     '--workspace-dir', '/work/native-logs']]
        staging = ['Render native config from approved settings and full brief.',
                   'Model endpoint/authentication is supplied by the trusted runtime, not this plan.']
    else:
        options = {k: selected[k] for k in ('AUTO_WRITE', 'CODE_REVIEW', 'BASE_REPO', 'VENUE')}
        run_model = ledger.get('run_model', MODEL)
        deepseek = run_model == 'deepseek-flash'
        relative = 'aris' if deepseek else 'reviewer-timeout-compat/aris'
        binary = Path(__file__).resolve().parents[3]/'tools/aris-code-v0.4.24'/relative
        expected = ('5d0dc25523b77fe05e44c205d4f33db8792b38c1f72c09bb8ce16e33721b39a7' if deepseek
                    else '88488832b5900d06f0503eda758dbd23210fbb294fe2cf6cbb321773ccee7597')
        if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
            raise ValueError('selected ARIS binary mismatch')
        prefix = [] if deepseek else ['env', 'ARIS_REVIEWER_TIMEOUT_SECONDS=1200']
        commands = [[*prefix, '/tools/'+relative, *aris_argv(brief, options, run_model)[1:]]]
        staging = ['Verify selected native bundled skill/reviewer routing and paper stages.']
    return {'status': 'NATIVE_COMMAND_PLAN_NOT_EXECUTABLE', 'system': system,
            'execution_authorized': False, 'processes_started': 0,
            'selection': policy, 'native_argv': commands,
            'shell_preview_inside_future_sandbox': ' && '.join(shlex.join(c) for c in commands),
            'approved_system_settings': selected,
            'whole_run_timeout_seconds': settings['whole_run_timeout_seconds'],
            'native_cwd': '/work/project', 'staging_requirements': staging,
            'model': ledger.get('run_model', MODEL), 'brief_sha256': hashlib.sha256(brief.encode()).hexdigest(),
            'credential_contract': {
                'model': 'trusted audited local endpoint and ephemeral token only',
                'semantic_scholar': 'user supplies S2_API_KEY for v1/v2; authentication integration pending'},
            'production_requirements': ['verified isolation/egress and dependency staging',
                'verified audit/resource/native-stage/compilation/archive lifecycle',
                'shared single-run lock held through cleanup and archive',
                'final snapshot bindings and separate execution approval'],
            'final_snapshot_frozen': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system', required=True, choices=SYSTEMS)
    parser.add_argument('--approvals', required=True, type=Path)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--brief', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.approvals.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.expected_sha256:
        parser.error('approval ledger hash mismatch')
    plan = build(json.loads(raw), args.system, args.brief.read_text())
    plan['approval_ledger_sha256'] = args.expected_sha256
    plan['builder_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open('x') as stream:
        json.dump(plan, stream, indent=2)
        stream.write('\n')
    print('Wrote one command plan; no process started: '+str(args.output))


if __name__ == '__main__':
    main()
