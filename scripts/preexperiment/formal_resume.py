"""Copy an archived formal run and select its native resume entry, never launch."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build_single_system_plan import build
from native_config import arbor_config
from prepare_inputs import ROOT, BRIEF_SHA
from staged_offline import workspace_path


def tag(value):
    if not value or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in value):
        raise ValueError('simple run identity required')
    return value


def binding(system, source_run_id, native_run_id=None):
    source_run_id = tag(source_run_id)
    source = workspace_path(ROOT/'offline-verification'/source_run_id)
    receipt = ROOT/'admin_review'/source_run_id/'receipt.json'
    saved = json.loads(receipt.read_text())
    if saved.get('kind') != 'formal_single_system_run' or saved.get('system') != system:
        raise ValueError('archived formal run of the same system required')
    if hashlib.sha256((source/'project/RESEARCH_BRIEF.md').read_bytes()).hexdigest() != BRIEF_SHA:
        raise ValueError('formal resume brief mismatch')
    if system == 'arbor':
        paths = ['native-logs/run/.coordinator/'+n for n in ('checkpoint.json','messages.jsonl','idea_tree.json')]
    elif system == 'aris-code':
        native_run_id = tag(native_run_id)
        paths = ['project/.aris/runs/'+native_run_id+'.json']
    else:
        raise ValueError('ARIS or Arbor required')
    return {'source_run_id':source_run_id,'native_run_id':native_run_id,
            'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
            'state_sha256':{p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in paths}}


def stage(ledger, approval, workspace):
    if approval.get('artifact_classification') != 'diagnostic_resumed':
        raise ValueError('resumed formal state must be classified diagnostic_resumed')
    resume = approval['native_resume']
    actual = binding(approval['system'], resume['source_run_id'], resume.get('native_run_id'))
    if actual != resume:
        raise ValueError('archived resume binding mismatch')
    source = workspace_path(ROOT/'offline-verification'/resume['source_run_id'])
    previous = json.loads((ROOT/'admin_review'/resume['source_run_id']/'evidence/parameter-ledger.json').read_text())
    previous_settings = json.loads(json.dumps(previous['approved_settings']))
    current_settings = json.loads(json.dumps(ledger['approved_settings']))
    # A resumed Arbor run may use only these explicitly approved operational
    # controls to request finalization.  Scientific inputs and settings remain
    # byte-for-byte bound to the stopped run.
    if approval['system'] == 'arbor' and approval.get('system_overrides'):
        for key in ('max_cycles', 'time_budget', 'budget_policy'):
            current_settings['arbor'].pop(key, None)
            previous_settings['arbor'].pop(key, None)
    if previous_settings != current_settings:
        raise ValueError('resume must preserve approved scientific settings')
    plan = build(ledger, approval['system'], (source/'project/RESEARCH_BRIEF.md').read_text())
    workspace = workspace_path(workspace); workspace.mkdir(mode=0o700)
    for entry in source.iterdir():
        if entry.name == 'venv':
            continue
        target = workspace/entry.name
        subprocess.run(['/usr/bin/cp', '-a', '--reflink=auto', str(entry), str(target)], check=True)
    if approval['system'] == 'arbor':
        settings = ledger['approved_settings']['arbor']
        config = arbor_config((source/'project/RESEARCH_BRIEF.md').read_text(),
                              'http://127.0.0.1:18080/v1',
                              'offline-placeholder-not-a-provider-key')
        config.update(max_cycles=settings['max_cycles'],
                      executor_max_turns=settings['executor_max_turns'],
                      max_turns=settings['coordinator_max_turns'],
                      max_retries=settings['node_resume_max_retries'])
        if 'time_budget' in settings:
            config['time_budget'] = settings['time_budget']
        if 'budget_policy' in settings:
            config['budget_policy'] = settings['budget_policy']
        (workspace/'project/research_config.yaml').write_text(json.dumps(config,indent=2)+'\n')
        # Native resume still requires a clean Git view. These are preserved
        # run artifacts created outside Git by the stopped Arbor session.
        info = workspace/'project/.git/info'
        if (workspace/'project/.git').is_dir():
            info.mkdir(parents=True, exist_ok=True)
            exclude = info/'exclude'
            existing = exclude.read_text() if exclude.exists() else ''
            additions = ''.join(line for line in ('/data/\n','/outputs/\n','/probe/\n')
                                if line not in existing)
            exclude.write_text(existing + additions)
        if approval.get('finalization_requested') is True:
            message = {
                'role': 'user',
                'content': ('The user requests early finalization now. Do not launch any new '
                            'research branches or executors. Use the existing completed evidence, '
                            'select and merge the best valid result if appropriate, then complete '
                            'the native final report and paper workflow.')}
            with (workspace/'native-logs/run/.coordinator/messages.jsonl').open('a') as stream:
                stream.write(json.dumps(message,ensure_ascii=False)+'\n')
        plan['native_argv'][0] += ['--resume','--','--allow-non-base-branch']
    else:
        plan['native_argv'][0][-1] += '\n— resume '+resume['native_run_id']
    plan.update(resume_environment=str(source/'venv'),artifact_classification='diagnostic_resumed')
    (workspace/'formal-resume.json').write_text(json.dumps(resume,indent=2)+'\n')
    return plan
