#!/usr/bin/env python3
"""Materialize new byte-verified input views, never modify frozen sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path('/home/zf/projects/autoresearch')
BRIEF_SHA = '8610326c0c4796cff741383c2097bb71b4afcc8159421a71b4922d9835ecf310'
PDF_SHA = 'f284446e3f3346f5d11fe2608251c91a5b5c4ec92a130a66dcea7e8013300c6f'
SYSTEMS = ('ai-scientist-v1', 'ai-scientist-v2', 'arbor', 'aris-code')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def safe_file(root, relative):
    p = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('unsafe relative input')
    if p.resolve() != p or not p.is_file():
        raise ValueError('input must be a regular file without symlinks')
    return p

def prepare(dest):
    brief = ROOT / 'Auto-Research/common_start_package/protocol-v0.9/RESEARCH_BRIEF.md'
    pdf = ROOT / 'common/seed_papers/sam3d-cvpr2026-accepted/SAM_3D_CVPR2026_accepted.pdf'
    if digest(brief) != BRIEF_SHA or digest(pdf) != PDF_SHA:
        raise ValueError('frozen input mismatch')
    dest.mkdir(parents=True, exist_ok=False)
    common = dest / 'common'; common.mkdir()
    shutil.copyfile(brief, common / 'RESEARCH_BRIEF.md')
    shutil.copyfile(ROOT/'admin_review/process-implementation-20260907/input-drafts/common/MATERIALS.md',common/'MATERIALS.md')
    (common / 'seed_papers').mkdir()
    shutil.copyfile(pdf, common / 'seed_papers/SAM_3D_CVPR2026_accepted.pdf')
    data_root = ROOT / 'common/datasets/development/protocol-v0.9'
    data = json.loads((data_root / 'manifest.json').read_text())
    if data['total'] != 190 or len(data['pairs']) != 190:
        raise ValueError('development count mismatch')
    # New visible index contains only scientific data identifiers, not protocol fields.
    rows = []
    for row in data['pairs']:
        if row.get('split') != 'development': raise ValueError('unexpected split')
        visible = {k:v for k,v in row.items() if k not in {'split', 'protocol'}}
        for key in ('rgb_rel', 'mask_rel', 'iid_rel'):
            if key not in row: continue
            src = safe_file(data_root, row[key]); target = common / 'data' / row[key]
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, target)
        rows.append(visible)
    (common / 'data/index.json').write_text(json.dumps(rows, indent=2)+'\n')
    template = ROOT / 'Auto-Research/templates/cvpr/CVPR2026-v1'
    for src in sorted(template.rglob('*')):
        if src.is_symlink(): raise ValueError('template symlink requires review')
        if src.is_file() and src.name != 'MANIFEST.md':
            target = common / 'latex' / src.relative_to(template)
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src,target)
    # Native representation is explicit and lossless. Parameters are added later.
    text = brief.read_text()
    drafts = ROOT / 'admin_review/process-implementation-20260907/input-drafts/native'
    for system in SYSTEMS:
        out = dest / system; out.mkdir()
        shutil.copyfile(brief, out/'RESEARCH_BRIEF.md')
        if system == 'ai-scientist-v1':
            prompt = json.loads((drafts/'v1.prompt.json').read_text())
            if prompt['task_description'] != text: raise ValueError('v1 brief drift')
            (out/'prompt.json').write_text(json.dumps(prompt,indent=2)+'\n')
        elif system == 'ai-scientist-v2': shutil.copyfile(brief,out/'workshop.md')
        elif system == 'arbor':
            # JSON is valid YAML and avoids scalar/newline conversion.
            (out/'task.yaml').write_text(json.dumps({'task':text},indent=2)+'\n')
        else:
            # The native skill passes $ARGUMENTS into idea-discovery verbatim.
            (out/'pipeline-input.txt').write_text('/research-pipeline '+text)
    files = {str(p.relative_to(dest)):digest(p) for p in sorted(dest.rglob('*')) if p.is_file()}
    manifest = {'status':'MATERIALIZED_PARTIAL_CODE_BASELINE_PENDING', 'files':files,
                'shared_mount':'common -> /materials for every system',
                'system_mount':'<system> -> /input; no other system view',
                'brief_sha256':BRIEF_SHA,'seed_pdf_sha256':PDF_SHA}
    # Manifest is operator-only; mount only common and the selected system subdir.
    (dest/'operator-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'files':len(files),'development_pairs':len(rows),'status':manifest['status']}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().dest)))
