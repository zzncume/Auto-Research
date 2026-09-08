"""Per-run writable clone of a rebuilt environment; original remains unchanged.

Mount the clone at the original in-sandbox path so existing script shebangs work.
No downloads, package installation, credentials or process launches on import.
"""
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, urlunsplit

from staged_offline import PROFILES, command, workspace_path


def inventory(environment):
    packages = []
    for meta in sorted(Path(environment).glob('lib/python*/site-packages/*.dist-info/METADATA')):
        fields = {}
        for line in meta.read_text(errors='replace').splitlines():
            if line.startswith(('Name: ', 'Version: ')):
                key, value = line.split(': ', 1); fields[key] = value
            if not line:
                break
        item = {'name': fields.get('Name'), 'version': fields.get('Version'),
                'metadata_sha256': hashlib.sha256(meta.read_bytes()).hexdigest()}
        origin = meta.parent/'direct_url.json'
        if origin.is_file():
            url = urlsplit(json.loads(origin.read_text()).get('url', ''))
            # Never record URL credentials, queries or fragments.
            item['direct_source'] = urlunsplit((url.scheme, url.hostname or '', url.path, '', ''))
        packages.append(item)
    return packages


def clone(system, workspace, evidence):
    workspace = workspace_path(workspace)
    source = PROFILES[system][1]
    evidence = Path(evidence).resolve()
    if evidence == workspace or workspace in evidence.parents:
        raise ValueError('environment evidence must be outside native workspace')
    evidence.mkdir(parents=True, exist_ok=True)
    target = workspace/'venv'; target.mkdir()
    initial = inventory(source) if source else []
    with (evidence/'environment-initial.json').open('x') as stream:
        json.dump({'source_profile': system, 'packages': initial,
                   'source_preserved': True, 'copy_mode': 'reflink-or-independent-copy' if source else 'new-stdlib-venv'}, stream, indent=2)
    if source:
        subprocess.run(['/usr/bin/cp', '-a', '--reflink=auto', str(source)+'/.', str(target)], check=True)
    else:
        # ARIS is a standalone binary; provide a clean writable Python tools env.
        subprocess.run(['/usr/bin/python3', '-m', 'venv', '--without-pip', str(target)], check=True)
    return target


def writable_command(system, workspace, argv, command_builder=None):
    workspace = workspace_path(workspace)
    source = PROFILES[system][1]
    target = workspace/'venv'
    if not (target/'pyvenv.cfg').is_file() or target.is_symlink():
        raise ValueError('prepared per-run environment required')
    args = (command_builder or command)(system, workspace, argv)
    if source is None:
        split = args.index('--')
        args[split:split] = ['--bind', str(target), '/env', '--setenv', 'PATH', '/env/bin:/usr/bin:/bin']
        return args
    binding = ['--ro-bind', str(source), str(source)]
    for index in range(len(args)-2):
        if args[index:index+3] == binding:
            args[index:index+3] = ['--bind', str(target), str(source)]
            return args
    raise ValueError('expected environment mount missing')


def pip_bootstrap_command(system, workspace, command_builder=None):
    source_python = (PROFILES['ai-scientist-v1'][1]/'bin/python').resolve(strict=True)
    wheels = list((source_python.parent.parent/'lib/python3.11/ensurepip/_bundled').glob('pip-*-py3-none-any.whl'))
    if len(wheels) != 1:
        raise ValueError('one bundled offline pip wheel required')
    wheel = wheels[0]; mounted = '/bootstrap/'+wheel.name
    args = writable_command(system, workspace, ['/env/bin/python', '-m', 'pip', 'install',
            '--no-index', '--no-deps', '--disable-pip-version-check', mounted], command_builder=command_builder)
    split = args.index('--')
    args[split:split] = ['--ro-bind', str(wheel), mounted, '--setenv', 'PYTHONPATH', mounted]
    return args


def finish(workspace, evidence):
    packages = inventory(Path(workspace)/'venv')
    with (Path(evidence)/'environment-final.json').open('x') as stream:
        json.dump({'packages': packages, 'scope': 'installed metadata snapshot; command logs retained separately'}, stream, indent=2)
    return packages
