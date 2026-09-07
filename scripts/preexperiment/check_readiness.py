#!/usr/bin/env python3
"""Read-only preparation check; never runs an experiment or approves parameters."""
import hashlib
import json
from pathlib import Path
from prepare_inputs import ROOT,BRIEF_SHA,PDF_SHA,digest

def check():
    proof=ROOT/'admin_review/preexperiment-20260907'
    checks={};missing=[]
    inputs=[('brief',ROOT/'Auto-Research/common_start_package/protocol-v0.9/RESEARCH_BRIEF.md',BRIEF_SHA),
            ('seed_pdf',ROOT/'common/seed_papers/sam3d-cvpr2026-accepted/SAM_3D_CVPR2026_accepted.pdf',PDF_SHA)]
    for name,path,expected in inputs:
        checks[name]=path.is_file() and digest(path)==expected
    wrapper=digest(Path(__file__).with_name('offline_wrapper.py'))
    for name in ('v1','v2','v2-ideation','arbor','aris'):
        p=proof/(name+'-runtime-help.json')
        try:
            r=json.loads(p.read_text())
            ok=r['exit_code']==0 and not r['timed_out'] and r['wrapper_sha256']==wrapper
            ok=ok and r['network']=='unshared' and r['gpu_devices']==0
        except (OSError,ValueError,KeyError):ok=False
        checks[name+'_cli']=ok
    # These receipts must be produced by actual integration/build verification.
    # CLI/help and unit tests are deliberately insufficient substitutes.
    for gate in ('sam3d_runtime','production_isolation_e2e','native_launch_archive_e2e','native_adapters_mock'):
        p=proof/(gate+'.json')
        ok=False
        if p.is_file() and not p.is_symlink():
            try:
                data=json.loads(p.read_text());refs=data['evidence_refs']
                ok=data['result']=='pass' and bool(refs)
                for ref in refs:
                    f=Path(ref['path'])
                    ok=ok and f.is_absolute() and not f.is_symlink() and f.resolve()==f and digest(f)==ref['sha256']
            except (OSError,ValueError,KeyError,TypeError):ok=False
        checks[gate]=ok
    checks['parameter_review_exists']=(proof/'parameters.pending.json').is_file()
    missing=[name for name,ok in checks.items() if not ok]
    return {'status':'BLOCKED' if missing else 'READY_FOR_PREEXPERIMENT_PARAMETER_APPROVAL',
            'checks':checks,'missing':missing,'parameters_frozen':False,
            'preexperiment_started':False,'model_api_called':False,'gpu_used':False}

if __name__=='__main__':
    result=check();print(json.dumps(result,indent=2));raise SystemExit(bool(result['missing']))
