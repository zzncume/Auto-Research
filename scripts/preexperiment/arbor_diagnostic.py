"""Hash-bound Arbor CPU diagnostic using native coordinator and executor."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess

from native_config import MODEL, model_environment
from offline_wrapper import command as offline_command
from prepare_inputs import ROOT
from staged_offline import PROFILES, workspace_path
from run_environment import writable_command


def stage(approval, workspace):
    if approval['system'] != 'arbor' or approval['use_gpu'] is not False:
        raise ValueError('Arbor CPU diagnostic required')
    path = (ROOT/'ai-context-hub'/approval['task_path']).resolve(strict=True)
    if not path.is_relative_to(ROOT/'ai-context-hub/projects/autoresearch') or path.suffix != '.md':
        raise ValueError('approved project task required')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != approval['task_sha256']:
        raise ValueError('diagnostic task mismatch')
    options = approval['native_options']
    required = {'max_cycles', 'executor_max_turns', 'coordinator_max_turns', 'node_resume_max_retries'}
    if set(options) != required or any(type(v) is not int or v < 1 for v in options.values()):
        raise ValueError('explicit native settings required')
    workspace = workspace_path(workspace); workspace.mkdir(mode=0o700)
    project = workspace/'project'; project.mkdir()
    (project/'RESEARCH_BRIEF.md').write_bytes(raw)
    (project/'.gitignore').write_text('research_config.yaml\n.coordinator/\n__pycache__/\n')
    config = {'task': raw.decode(), 'meta_model': MODEL,
              'llm': {'provider': 'litellm', 'model': MODEL, 'llm_timeout': 1200,
                      'base_url': 'http://127.0.0.1:18080/v1', 'api_key': 'pending-local-binding'},
              'max_cycles': options['max_cycles'], 'executor_max_turns': options['executor_max_turns'],
              'max_turns': options['coordinator_max_turns'], 'max_retries': options['node_resume_max_retries']}
    (project/'research_config.yaml').write_text(json.dumps(config, indent=2)+'\n')
    # Native Arbor branches/worktrees require a repository with an initial HEAD.
    def git(*args):
        subprocess.run(['git', '-C', str(project), *args], check=True, capture_output=True)
    git('init', '-b', 'main'); git('config', 'user.name', 'Arbor diagnostic')
    git('config', 'user.email', 'arbor@localhost')
    git('add', '--', 'RESEARCH_BRIEF.md', '.gitignore')
    git('commit', '-m', 'Initialize approved diagnostic task')
    argv = ['/env/bin/python', '-m', 'arbor.run', '--cwd', '/work/project',
            '--config', '/work/project/research_config.yaml', '--run-name', 'run',
            '--workspace-dir', '/work/native-logs']
    return {'kind': approval['kind'], 'native_argv': [argv],
            'task_sha256': approval['task_sha256'], 'formal_brief_used': False}


def command(system, workspace, argv):
    if system != 'arbor':
        raise ValueError('Arbor diagnostic only')
    source, environment = PROFILES[system]
    args = offline_command(source, workspace_path(workspace), [], environment)
    extra = ['--symlink', str(environment), '/env', '--symlink', '/source', '/engine',
             '--chdir', '/work/project', '--setenv', 'PATH', '/env/bin:/usr/bin:/bin',
             '--setenv', 'PYTHONPATH', '/engine', '--setenv', 'PYTHONNOUSERSITE', '1',
             '--setenv', 'PYTHONUNBUFFERED', '1',
             '--ro-bind', '/etc/ssl/certs', '/etc/ssl/certs',
             '--setenv', 'SSL_CERT_FILE', '/etc/ssl/certs/ca-certificates.crt',
             '--ro-bind', str(ROOT/'Auto-Research/scripts/preexperiment'), '/runtime-tools',
             '--ro-bind', str(ROOT/'tools/tokenizer-cache'), '/tokenizer-cache',
             '--setenv', 'TIKTOKEN_CACHE_DIR', '/tokenizer-cache']
    return args[:-1]+extra+['--']+argv


def bind(system, workspace, native_argv, sockets, local_token, seed):
    args = writable_command(system, workspace,
        ['/env/bin/python', '/runtime-tools/transport_bootstrap.py', *native_argv], command_builder=command)
    if 'model' not in sockets:
        raise ValueError('audited model gateway required')
    extra = []
    for name, path in sockets.items():
        if name not in ('model', 'literature', 'egress') or not stat.S_ISSOCK(Path(path).stat().st_mode):
            raise ValueError('selected Unix transport required')
        extra += ['--ro-bind', str(path), '/transport/'+name+'.sock']
    env = model_environment(system, 'http://127.0.0.1:18080/v1', local_token)
    env.update(RESEARCH_LOCAL_TOKEN=local_token, RESEARCH_SEED=str(seed), PYTHONHASHSEED=str(seed),
               GIT_AUTHOR_NAME='Arbor diagnostic', GIT_AUTHOR_EMAIL='arbor@localhost',
               GIT_COMMITTER_NAME='Arbor diagnostic', GIT_COMMITTER_EMAIL='arbor@localhost')
    if 'egress' in sockets:
        env.update(HTTP_PROXY='http://127.0.0.1:18082', HTTPS_PROXY='http://127.0.0.1:18082',
                   http_proxy='http://127.0.0.1:18082', https_proxy='http://127.0.0.1:18082',
                   NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
    config_path = Path(workspace)/'project/research_config.yaml'
    config = json.loads(config_path.read_text()); config['llm']['api_key'] = local_token
    config_path.write_text(json.dumps(config, indent=2)+'\n')
    for key, value in env.items():
        extra += ['--setenv', key, value]
    split = args.index('--'); args[split:split] = extra
    return args
