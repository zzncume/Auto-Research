#!/usr/bin/env python3
"""Run official single-frame SAM3D reconstruction on the supplied inputs."""
import argparse
import json
import os
from pathlib import Path
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out_dir',required=True)
    p.add_argument('--materials',type=Path,default=Path('/materials'))
    p.add_argument('--validate-inputs',action='store_true')
    a=p.parse_args();rows=json.loads((a.materials/'data/index.json').read_text())
    for row in rows:
        for field in ('rgb_rel','mask_rel'):
            path=a.materials/'data'/row[field]
            if not path.is_file():raise FileNotFoundError(field)
    if a.validate_inputs:
        print(json.dumps({'input_pairs':len(rows),'inference_performed':False}));return
    # The caller supplies the reconstruction seed.
    seed=int(os.environ['RESEARCH_SEED'])
    code=a.materials/'code';sys.path[:0]=[str(code),str(code/'notebook')]
    from inference import Inference,load_image
    import numpy as np
    from PIL import Image
    engine=Inference(str(code/'checkpoints/hf/pipeline.yaml'),compile=False)
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    entries=[]
    for row in rows:
        image=load_image(str(a.materials/'data'/row['rgb_rel']))
        mask=np.array(Image.open(a.materials/'data'/row['mask_rel']).convert('L'))>0
        result=engine(image,mask,seed=seed)
        name=row['frame_id']+'.ply';result['gs'].save_ply(str(out/name))
        entries.append({'frame_id':row['frame_id'],'splat':name})
        (out/'outputs.json').write_text(json.dumps(entries,indent=2)+'\n')
    (out/'final_info.json').write_text(json.dumps({'outputs':entries,'input_pairs':len(rows)},indent=2)+'\n')

if __name__=='__main__':main()
