#!/usr/bin/env python3
"""Copy only selected development splats and official code into a new view."""
import json
from pathlib import Path
import shutil
from prepare_inputs import ROOT,digest,safe_file

def extend(dest):
    common=dest/'common'
    manifest=json.loads((dest/'operator-manifest.json').read_text())
    data=json.loads((common/'data/index.json').read_text())
    ids=[r['frame_id'] for r in data]
    if len(ids)!=190 or len(set(ids))!=190:raise ValueError('unexpected development identities')
    baseline=ROOT/'runs/sam3d_baseline/development/splat'
    target=common/'baseline';target.mkdir(exist_ok=False)
    for fid in ids:
        src=safe_file(baseline,fid+'.ply')
        shutil.copyfile(src,target/(fid+'.ply'))
    code_root=ROOT/'common/sam3d/sam-3d-objects'
    code=common/'code';code.mkdir(exist_ok=False)
    for name in ('sam3d_objects','notebook','patching','environments'):
        src=code_root/name
        for p in sorted(src.rglob('*')):
            if '__pycache__' in p.parts:continue
            if p.is_symlink():raise ValueError('source symlink requires review')
            if not p.is_file():continue
            rel=p.relative_to(code_root);out=code/rel
            out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    for name in ('demo.py','pyproject.toml','requirements.txt','requirements.inference.txt',
                 'requirements.p3d.txt','LICENSE'):
        shutil.copyfile(safe_file(code_root,name),code/name)
    # Checkpoints stay at a separate explicitly read-only mount; no bulk duplicate.
    weights=code_root/'checkpoints/hf'
    weight_index={}
    for p in sorted(weights.iterdir()):
        if p.is_symlink() or not p.is_file():raise ValueError('unexpected checkpoint entry')
        weight_index[p.name]={'bytes':p.stat().st_size,'sha256':digest(p)}
    manifest['checkpoint_mount']={'source':str(weights),'target':'/materials/code/checkpoints/hf',
                                  'readonly':True,'files':weight_index}
    manifest['files']={str(p.relative_to(dest)):digest(p) for p in sorted(dest.rglob('*'))
                      if p.is_file() and p.name!='operator-manifest.json'}
    manifest['status']='MATERIALIZED_CHECKPOINT_MOUNT_PENDING_RUNTIME_VALIDATION'
    (dest/'operator-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'development_splats':len(ids),'checkpoints':len(weight_index),
                      'files':len(manifest['files']),'status':manifest['status']}))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',type=Path,required=True)
    extend(p.parse_args().dest)
