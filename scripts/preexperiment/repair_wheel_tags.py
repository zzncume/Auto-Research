#!/usr/bin/env python3
"""Correct two verified upstream WHEEL metadata errors in a new environment only.

Official PyPI filenames and isolated CPU probes establish the actual tags.
No package code/binary/version changes. Original metadata is retained separately.
"""
import argparse,base64,csv,hashlib,io,json,os
from pathlib import Path

ROOT=Path('/home/zf/projects/autoresearch')
FIXES={
 'bpy-4.3.0.dist-info':('701d82ea459892bc8efd2e760e6ea2c54d7753a392288fbf67d6bffaaef37cc8',
     'cp39-cp39-manylinux_2_28_x86_64','cp311-cp311-manylinux_2_28_x86_64'),
 'decord-0.6.0.dist-info':('d24f09731316657ed32488ba245812cbb5047342b148776a371264e69966d856',
     'cp36-cp36m-manylinux2010_x86_64','py3-none-manylinux2010_x86_64')}

def sha(b):return hashlib.sha256(b).hexdigest()

def atomic_write(path,data):
    # uv may hardlink metadata to its cache: never edit that inode in place.
    temp=path.with_name(path.name+'.codex-repair-tmp')
    with temp.open('xb') as f:f.write(data)
    os.replace(temp,path)

def repair(environment,backup):
    environment=environment.resolve(strict=True)
    if ROOT/'envs-rebuilt' not in environment.parents:raise ValueError('only rebuilt environment allowed')
    site=environment/'lib/python3.11/site-packages'
    plans=[]
    for name,(old_sha,old_tag,new_tag) in FIXES.items():
        wheel=site/name/'WHEEL';record=site/name/'RECORD'
        for p in (wheel,record):
            if p.resolve()!=p or not p.is_file():raise ValueError('metadata path must not be a link')
        before=wheel.read_bytes();old=('Tag: '+old_tag).encode();new=('Tag: '+new_tag).encode()
        if sha(before)!=old_sha:
            if before.count(new)==1 and sha(before.replace(new,old))==old_sha:continue
            raise ValueError('unrecognized upstream WHEEL')
        if before.count(old)!=1:raise ValueError('unexpected tag count')
        after=before.replace(old,new);record_before=record.read_bytes()
        rows=list(csv.reader(io.StringIO(record_before.decode())));matches=[row for row in rows if row[0]==name+'/WHEEL']
        if len(matches)!=1:raise ValueError('WHEEL must have exactly one RECORD row')
        expected='sha256='+base64.urlsafe_b64encode(hashlib.sha256(before).digest()).decode().rstrip('=')
        if matches[0][1]!=expected:raise ValueError('original WHEEL does not match RECORD')
        matches[0][1]='sha256='+base64.urlsafe_b64encode(hashlib.sha256(after).digest()).decode().rstrip('=')
        matches[0][2]=str(len(after));out=io.StringIO();csv.writer(out,lineterminator='\n').writerows(rows)
        plans.append((name,wheel,record,before,after,record_before,out.getvalue().encode()))
    if not plans:return {'status':'already_repaired'}
    backup.mkdir(parents=True,exist_ok=False);result=[]
    for name,wheel,record,before,after,rb,ra in plans:
        b=backup/name;b.mkdir();(b/'WHEEL').write_bytes(before);(b/'RECORD').write_bytes(rb)
        atomic_write(wheel,after);atomic_write(record,ra)
        result.append({'distribution':name,'original_wheel_metadata_sha256':sha(before),'new_wheel_metadata_sha256':sha(after),
                       'original_record_sha256':sha(rb),'new_record_sha256':sha(ra),'binary_code_changed':False})
    (backup/'repair-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    return {'status':'repaired','distributions':len(result),'binary_code_changed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--environment',type=Path,required=True);p.add_argument('--backup',type=Path,required=True)
    a=p.parse_args();print(json.dumps(repair(a.environment,a.backup)))
