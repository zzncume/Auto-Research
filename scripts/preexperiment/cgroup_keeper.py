#!/usr/bin/env python3
"""Idle keeper for an explicitly approved, systemd-delegated cgroup.

Never starts a research process, opens a provider connection or accesses a GPU.
Activation is only possible inside the exact dedicated service cgroup.
"""
import argparse,json,os,signal
from pathlib import Path

UNIT='autoresearch-zf.service'
CONTROLLERS={'cpu','memory','pids'}


def validate_group(group,pid):
    if group.resolve(strict=True)!=group or group.name!=UNIT:
        raise ValueError('must run inside the dedicated canonical service cgroup')
    available=set((group/'cgroup.controllers').read_text().split())
    if not CONTROLLERS.issubset(available):raise ValueError('required controllers not delegated')
    members={int(x) for x in (group/'cgroup.procs').read_text().split()}
    if members!={pid}:raise ValueError('refuse to move or interfere with another process')
    if (group/'keeper').exists() or (group/'runs').exists():raise ValueError('existing delegation tree requires operator review')


def activate(group,pid):
    validate_group(group,pid)
    keeper=group/'keeper';keeper.mkdir()
    (keeper/'cgroup.procs').write_text(str(pid))
    (group/'cgroup.subtree_control').write_text('+cpu +memory +pids')
    runs=group/'runs';runs.mkdir()
    (runs/'cgroup.subtree_control').write_text('+cpu +memory +pids')
    return runs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--activate-delegation',action='store_true')
    p.add_argument('--status-file',type=Path,required=True)
    a=p.parse_args()
    if os.getuid()!=1001:raise ValueError('expected zf UID 1001; no root execution')
    rows=[line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::')]
    if len(rows)!=1 or '..' in Path(rows[0]).parts:raise ValueError('cgroup v2 membership unavailable')
    group=Path('/sys/fs/cgroup')/rows[0].lstrip('/')
    if not a.activate_delegation:
        print(json.dumps({'unit':UNIT,'activation_requested':False,'controllers':sorted(CONTROLLERS)}));return
    status=a.status_file.absolute()
    allowed=Path('/home/zf/projects/autoresearch/admin_review/preexperiment-20260907')
    if status.parent.resolve()!=allowed or status.exists() or status.is_symlink():raise ValueError('status destination must be new and operator-only')
    runs=activate(group,os.getpid())
    with status.open('x') as f:json.dump({'unit':UNIT,'run_cgroup_root':str(runs),'keeper_pid':os.getpid(),'controllers':sorted(CONTROLLERS),'research_processes_started':0},f,indent=2)
    status.chmod(0o600)
    while True:signal.pause()

if __name__=='__main__':main()
