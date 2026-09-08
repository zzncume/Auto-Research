"""Stage selected native inputs and build the actual material-view offline boundary.

No live mode, GPU mount, credential loading, download or native process launch.
Only new CPU verification workspaces are accepted in this preparation version.
"""
import json
from pathlib import Path
import re
import shutil

from build_single_system_plan import build
from native_config import arbor_config, MODEL
from offline_wrapper import command as offline_command
from prepare_inputs import ROOT, safe_file

VIEW = ROOT/'inputs-prepared/preexperiment-20260907'
SOURCES = ROOT/'systems-prepared/preexperiment-20260907'
ENVS = ROOT/'envs-rebuilt/preexperiment-20260907'
PROFILES = {
    'ai-scientist-v1': (SOURCES/'ai-scientist-v1', ENVS/'v1'),
    'ai-scientist-v2': (SOURCES/'ai-scientist-v2', ENVS/'v2'),
    'arbor': (SOURCES/'arbor', ENVS/'arbor'),
    'aris-code': (ROOT/'tools/aris-code-v0.4.24', None),
}


def workspace_path(workspace):
    workspace = Path(workspace).absolute()
    if (workspace.resolve() != workspace or ROOT/'offline-verification' not in workspace.parents):
        raise ValueError('new canonical offline workspace required')
    return workspace


def stage(ledger, system, workspace):
    source, environment = PROFILES[system]
    workspace = workspace_path(workspace)
    brief = safe_file(VIEW/system, 'RESEARCH_BRIEF.md').read_text()
    plan = build(ledger, system, brief)
    settings = ledger['approved_settings'][system]
    workspace.mkdir(mode=0o700)
    project = workspace/'project'; project.mkdir()
    # Copy only the selected native input, never the operator manifest or Hub.
    if system == 'ai-scientist-v1':
        target = project/'templates/autoresearch'
        target.parent.mkdir()
        for p in (VIEW/system).rglob('*'):
            if p.is_symlink():
                raise ValueError('native input symlink denied')
        shutil.copytree(VIEW/system, target)
    elif system == 'ai-scientist-v2':
        (project/'brief.md').write_text(brief)
        config = (source/'bfts_config.yaml').read_text()
        expected = {'num_workers': settings['num_workers'], 'num_seeds': settings['num_seeds']}
        expected.update({f'stage{i+1}_max_iters': value for i, value in enumerate(settings['stage_max_iters'])})
        for key, value in expected.items():
            if len(re.findall(r'^\s*'+re.escape(key)+r':\s*'+str(value)+r'\s*(?:#.*)?$', config, re.M)) != 1:
                raise ValueError('prepared config differs from approval: '+key)
        if any(model != MODEL for model in re.findall(r'^\s*model:\s*([^\s#]+)', config, re.M)):
            raise ValueError('mixed model in native config')
        (project/'bfts_config.yaml').write_text(config)
    elif system == 'arbor':
        config = arbor_config(brief, 'http://127.0.0.1:18080/v1', 'offline-placeholder-not-a-provider-key')
        config.update(max_cycles=settings['max_cycles'], executor_max_turns=settings['executor_max_turns'],
                      max_turns=settings['coordinator_max_turns'], max_retries=settings['node_resume_max_retries'])
        (project/'research_config.yaml').write_text(json.dumps(config, indent=2)+'\n')
    else:
        (project/'RESEARCH_BRIEF.md').write_text(brief)
    return plan


def command(system, workspace, argv):
    source, environment = PROFILES[system]
    workspace = workspace_path(workspace)
    if not (workspace/'project').is_dir():
        raise ValueError('staged native project required')
    for path in (VIEW/'common', VIEW/system):
        if path.resolve(strict=True) != path:
            raise ValueError('canonical input view required')
    base = offline_command(source, workspace, [], environment)
    assert base[-1] == '--'
    extra = ['--ro-bind', str(VIEW/'common'), '/materials',
             '--ro-bind', str(VIEW/system), '/input',
             '--symlink', '/source', '/engine', '--chdir', '/work/project',
             '--setenv', 'PYTHONPATH', '/engine', '--setenv', 'PYTHONNOUSERSITE', '1']
    if environment:
        extra += ['--symlink', str(environment), '/env', '--setenv', 'PATH', '/env/bin:/usr/bin:/bin']
    else:
        extra += ['--symlink', '/source', '/tools']
    return base[:-1]+extra+['--']+argv
