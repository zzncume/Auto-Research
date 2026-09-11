"""Assemble project runtime mounts and transports; never start a process.

No GPU mount or live authorization is provided by this preparation component.
"""
from pathlib import Path
import json
import shutil
import stat

from native_config import model_environment
from run_environment import writable_command
from staged_offline import command, ENVS, VIEW
from prepare_inputs import ROOT


def bind(system, workspace, native_argv, sockets, local_token, seed, model=None):
    python = '/env/bin/python'
    argv = [python, '/runtime-tools/transport_bootstrap.py', *native_argv]
    args = writable_command(system, workspace, argv)
    extra = ['--ro-bind', str(ROOT/'Auto-Research/scripts/preexperiment'), '/runtime-tools']
    if 'model' not in sockets:
        raise ValueError('audited model transport required')
    for name, path in sockets.items():
        if name not in ('model', 'literature', 'egress') or not stat.S_ISSOCK(Path(path).stat().st_mode):
            raise ValueError('expected selected Unix transport socket')
        extra += ['--ro-bind', str(path), '/transport/'+name+'.sock']
    env = model_environment(system, 'http://127.0.0.1:18080/v1', local_token, **({'model': model} if model else {}))
    if system == 'arbor':
        config_path = Path(workspace)/'project/research_config.yaml'
        config = json.loads(config_path.read_text())
        config['llm'].update(base_url='http://127.0.0.1:18080/v1', api_key=local_token, llm_timeout=1200.0)
        config_path.write_text(json.dumps(config, indent=2)+'\n')
    if system == 'arbor':
        env.update(GIT_AUTHOR_NAME='Arbor', GIT_AUTHOR_EMAIL='arbor@localhost',
                   GIT_COMMITTER_NAME='Arbor', GIT_COMMITTER_EMAIL='arbor@localhost')
    env.update(RESEARCH_LOCAL_TOKEN=local_token, RESEARCH_SEED=str(seed), PYTHONHASHSEED=str(seed))
    if system in ('ai-scientist-v1', 'ai-scientist-v2'):
        env.update(AUTORESEARCH_NATIVE_SYSTEM=system, AUTORESEARCH_LLM_TIMEOUT_SECONDS='1200',
                   PYTHONPATH='/runtime-tools:/source')
    if 'literature' in sockets:
        env['S2_API_KEY'] = 'managed-by-local-gateway'
    if 'egress' in sockets:
        env.update(HF_HUB_OFFLINE='0', TRANSFORMERS_OFFLINE='0', HF_HOME='/work/hf-home')
        env.update(HTTP_PROXY='http://127.0.0.1:18082', HTTPS_PROXY='http://127.0.0.1:18082',
                   http_proxy='http://127.0.0.1:18082', https_proxy='http://127.0.0.1:18082',
                   NO_PROXY='127.0.0.1,localhost', no_proxy='127.0.0.1,localhost')
    inference = ENVS/'sam3d'
    extra += ['--ro-bind', str(inference), str(inference), '--symlink', str(inference), '/inference']
    interpreter = (inference/'bin/python').resolve(strict=True)
    base = interpreter.parent.parent
    if base.is_relative_to(Path('/home/zf/.local/share/uv/python')):
        extra += ['--ro-bind', str(base), str(base)]
    checkpoints = ROOT/'common/sam3d/sam-3d-objects/checkpoints/hf'
    # bwrap cannot create a new checkpoint mountpoint inside an existing
    # read-only material bind. Prepare that directory in a per-run code copy.
    code = Path(workspace)/'runtime-code'
    if not code.exists():
        shutil.copytree(VIEW/'common/code', code, symlinks=True)
        (code/'checkpoints/hf').mkdir(parents=True, exist_ok=True)
    extra += ['--ro-bind', str(code), '/materials/code',
              '--ro-bind', str(checkpoints), '/materials/code/checkpoints/hf']
    extra += ['--ro-bind', str(ROOT/'common/hf-cache/models--Ruicheng--moge-vitl'),
              '/model-cache/models--Ruicheng--moge-vitl']
    extra += ['--ro-bind', str(ROOT/'common/torch-cache'), '/torch-cache']
    env['TORCH_HOME'] = '/torch-cache'
    env['HF_HUB_CACHE'] = '/model-cache'
    env['RESEARCH_INFERENCE_PYTHON'] = '/inference/bin/python'
    for key, value in env.items():
        extra += ['--setenv', key, value]
    split = args.index('--'); args[split:split] = extra
    return args
