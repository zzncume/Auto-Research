"""Bounded CPU-only verification lifecycle, never a research launcher.

Uses the existing network/PID/device namespace boundary. Logs stream to new
operator files; timeout kills the task's process group and reaps its supervisor.
No credentials, GPU mounts, parameter defaults or live execution mode exist.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from offline_wrapper import command


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(source, workspace, argv, evidence, environment=None, timeout=30):
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
        raise ValueError('verification timeout must be in (0, 60]')
    workspace = Path(workspace).resolve(strict=True)
    evidence = Path(evidence).absolute()
    if evidence.resolve() != evidence or evidence == workspace or workspace in evidence.parents or evidence in workspace.parents:
        raise ValueError('operator evidence must be separate and symlink-free')
    cmd = command(Path(source), workspace, argv, environment)
    evidence.mkdir(mode=0o700)  # never overwrite a previous attempt
    started = time.monotonic()
    hashes = {p.name: digest(p) for p in (Path(__file__), Path(__file__).with_name('offline_wrapper.py'))}
    timed_out = False
    with (evidence/'stdout').open('xb') as out, (evidence/'stderr').open('xb') as err:
        child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                 env={'PATH': '/usr/bin:/bin'}, start_new_session=True)
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Bubblewrap owns a PID namespace; killing it also tears down that
            # namespace, including descendants that created their own sessions.
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    record = {'kind': 'offline_lifecycle_verification', 'argv': argv,
              'exit_code': child.returncode, 'timed_out': timed_out,
              'wall_seconds': time.monotonic()-started, 'implementation_sha256': hashes,
              'network': 'unshared', 'gpu_devices': 0, 'parameters_frozen': False,
              'execution_scope': 'offline_command_not_research_evidence',
              'resource_accounting_complete': False,
              'cpu_seconds': None, 'peak_tree_rss_bytes': None,
              'resource_unknown_reason': 'No delegated cgroup; full-tree accounting not measured',
              'outputs': {name: digest(evidence/name) for name in ('stdout', 'stderr')}}
    with (evidence/'termination.json').open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    return record
