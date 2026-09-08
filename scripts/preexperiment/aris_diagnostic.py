"""Separate hash-bound CPU diagnostic task; never substitute the frozen brief."""
import hashlib
from pathlib import Path
import stat
import json
import shutil

from native_config import aris_diagnostic_argv, model_environment
from offline_wrapper import command as offline_command
from prepare_inputs import ROOT
from staged_offline import PROFILES, VIEW, workspace_path
from run_environment import writable_command


def stage(approval, workspace):
    if approval['system'] != 'aris-code' or approval['use_gpu'] is not False:
        raise ValueError('ARIS CPU diagnostic required')
    path = (ROOT/'ai-context-hub'/approval['task_path']).resolve(strict=True)
    if not path.is_relative_to(ROOT/'ai-context-hub/projects/autoresearch') or path.suffix != '.md':
        raise ValueError('approved project task document required')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != approval['task_sha256']:
        raise ValueError('approved diagnostic task mismatch')
    task = raw.decode()
    argv = aris_diagnostic_argv(task, approval['task_sha256'], approval['native_options'])
    compatibility = approval.get('reviewer_timeout_compatibility')
    if compatibility:
        binary = ROOT/'tools/aris-code-v0.4.24/reviewer-timeout-compat/aris'
        if hashlib.sha256(binary.read_bytes()).hexdigest() != compatibility['binary_sha256']:
            raise ValueError('reviewer compatibility binary mismatch')
        if compatibility['timeout_seconds'] != 1200:
            raise ValueError('reviewer compatibility timeout must be 1200 seconds')
        argv = ['env', 'ARIS_REVIEWER_TIMEOUT_SECONDS=1200',
                '/tools/reviewer-timeout-compat/aris', *argv[1:]]
    workspace = workspace_path(workspace); workspace.mkdir(mode=0o700)
    (workspace/'project').mkdir()
    resume = approval.get('native_resume')
    if resume:
        source_tag = resume['source_run_id']
        native_id = resume['native_run_id']
        if any(not v or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in v)
               for v in (source_tag, native_id)):
            raise ValueError('invalid native resume identity')
        source = ROOT/'offline-verification'/source_tag/'project'
        receipt = ROOT/'admin_review'/source_tag/'receipt.json'
        if not receipt.is_file():
            raise ValueError('resume requires completed parent archive')
        state = source/'.aris/runs'/(native_id+'.json')
        if hashlib.sha256(state.read_bytes()).hexdigest() != resume['state_sha256']:
            raise ValueError('native resume state mismatch')
        if (source/'RESEARCH_BRIEF.md').read_bytes() != raw:
            raise ValueError('native resume task mismatch')
        shutil.copytree(source, workspace/'project', dirs_exist_ok=True, symlinks=True)
        argv[-1] += '\n— resume '+native_id
        (workspace/'diagnostic-resume.json').write_text(json.dumps(resume, indent=2)+'\n')
    (workspace/'project/RESEARCH_BRIEF.md').write_bytes(raw)
    return {'kind': 'aris_simple_workflow_diagnostic', 'native_argv': [argv],
            'task_sha256': approval['task_sha256'], 'formal_brief_used': False}


def command(system, workspace, argv):
    if system != 'aris-code':
        raise ValueError('ARIS diagnostic only')
    workspace = workspace_path(workspace)
    args = offline_command(PROFILES[system][0], workspace, [])
    return args[:-1]+['--symlink', '/source', '/tools', '--chdir', '/work/project',
                     '--ro-bind', str(VIEW/'common/native-latex'), '/materials/native-latex',
                     '--ro-bind', '/etc/ssl/certs', '/etc/ssl/certs',
                     '--setenv', 'SSL_CERT_FILE', '/etc/ssl/certs/ca-certificates.crt',
                     '--ro-bind', str(ROOT/'Auto-Research/scripts/preexperiment'), '/runtime-tools',
                     '--setenv', 'PYTHONNOUSERSITE', '1', '--']+argv


def bind(system, workspace, native_argv, sockets, local_token, seed):
    args = writable_command(system, workspace,
                            ['/env/bin/python', '/runtime-tools/transport_bootstrap.py', *native_argv],
                            command_builder=command)
    if 'model' not in sockets:
        raise ValueError('audited model transport required')
    extra = []
    for name, path in sockets.items():
        if name not in ('model', 'literature', 'egress') or not stat.S_ISSOCK(Path(path).stat().st_mode):
            raise ValueError('selected Unix transport required')
        extra += ['--ro-bind', str(path), '/transport/'+name+'.sock']
    env = model_environment(system, 'http://127.0.0.1:18080/v1', local_token)
    env.update(RESEARCH_LOCAL_TOKEN=local_token, RESEARCH_SEED=str(seed), PYTHONHASHSEED=str(seed))
    if 'egress' in sockets:
        env.update(HTTP_PROXY='http://127.0.0.1:18082', HTTPS_PROXY='http://127.0.0.1:18082',
                   http_proxy='http://127.0.0.1:18082', https_proxy='http://127.0.0.1:18082',
                   NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
    for key, value in env.items():
        extra += ['--setenv', key, value]
    split = args.index('--'); args[split:split] = extra
    return args
