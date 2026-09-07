#!/usr/bin/env python3
"""CPU-only offline verification wrapper. Has no live launch or network mode."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import resource
from datetime import datetime,timezone

ROOT=Path('/home/zf/projects/autoresearch')

def command(source, workspace, argv, environment=None):
    roots=[ROOT/'systems-prepared', ROOT/'tools/aris-code-v0.4.24']
    source=source.resolve(strict=True);workspace=workspace.resolve(strict=True)
    if not any(source==r or r in source.parents for r in roots):
        raise ValueError('source outside prepared allowlist')
    if ROOT/'offline-verification' not in workspace.parents:
        raise ValueError('workspace outside offline verification root')
    if source in workspace.parents or workspace in source.parents:
        raise ValueError('source/workspace overlap')
    args=['/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session',
          '--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64',
          '--symlink','usr/bin','/bin','--proc','/proc','--dev','/dev',
          '--tmpfs','/tmp','--ro-bind',str(source),'/source',
          '--bind',str(workspace),'/work','--chdir','/work','--clearenv',
          '--setenv','HOME','/work','--setenv','PATH','/usr/bin:/bin',
          '--setenv','LANG','C.UTF-8','--setenv','CUDA_VISIBLE_DEVICES','',
          '--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','PYTHONPATH','/source',
          '--setenv','HF_HUB_OFFLINE','1','--setenv','TRANSFORMERS_OFFLINE','1',
          '--setenv','WANDB_MODE','offline']
    for fixed in ('/etc/texmf','/var/lib/texmf','/etc/fonts','/var/cache/fontconfig'):
        if Path(fixed).is_dir():args += ['--ro-bind',fixed,fixed]
    if environment:
        env=environment.resolve(strict=True)
        if ROOT/'envs-rebuilt' not in env.parents: raise ValueError('old environment denied')
        args += ['--ro-bind',str(env),str(env)]
        interpreter=(env/'bin/python').resolve(strict=True)
        if interpreter.is_relative_to(Path('/home/zf/.local/share/uv/python')):
            base=interpreter.parent.parent
            args += ['--ro-bind',str(base),str(base)]
    return args+['--']+argv

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--environment',type=Path)
    p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--timeout',type=int,default=60)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('argv',nargs=argparse.REMAINDER)
    a=p.parse_args();argv=a.argv[1:] if a.argv[:1]==['--'] else a.argv
    if not argv: p.error('command required')
    cmd=command(a.source,a.workspace,argv,a.environment)
    if a.dry_run: print(json.dumps(cmd));return
    if a.receipt.exists(): raise ValueError('receipt exists')
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    if a.workspace.resolve() in a.receipt.resolve().parents:
        raise ValueError('receipt must be outside child writable tree')
    start=time.monotonic();started=datetime.now(timezone.utc).isoformat()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        r=subprocess.run(cmd,timeout=a.timeout,capture_output=True,env={'PATH':'/usr/bin:/bin'})
        rc=r.returncode;out=r.stdout;err=r.stderr;timed_out=False
    except subprocess.TimeoutExpired as exc:
        rc=None;out=exc.stdout or b'';err=exc.stderr or b'';timed_out=True
    a.receipt.with_suffix('.stdout').write_bytes(out)
    a.receipt.with_suffix('.stderr').write_bytes(err)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    record={'kind':'offline_verification_only','argv':argv,'exit_code':rc,
            'wall_seconds':time.monotonic()-start,'timed_out':timed_out,
            'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
            'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'peak_rss_bytes':after.ru_maxrss*1024,'resource_scope':'waited_child_tree',
            'network':'unshared','gpu_devices':0,'formal_run':False}
    a.receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))
    raise SystemExit(0 if rc==0 else 1)

if __name__=='__main__':main()
