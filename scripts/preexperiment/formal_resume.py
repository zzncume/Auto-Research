"""Copy an archived formal run and select its native resume entry, never launch."""
import hashlib
import json
from pathlib import Path
import shutil
from build_single_system_plan import build
from prepare_inputs import ROOT, BRIEF_SHA
from staged_offline import workspace_path


def tag(value):
    if not value or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in value):
        raise ValueError('simple run identity required')
    return value


def binding(system, source_run_id, native_run_id=None):
    source_run_id = tag(source_run_id)
    source = workspace_path(ROOT/'offline-verification'/source_run_id)
    receipt = ROOT/'admin_review'/source_run_id/'receipt.json'
    saved = json.loads(receipt.read_text())
    if saved.get('kind') != 'formal_single_system_run' or saved.get('system') != system:
        raise ValueError('archived formal run of the same system required')
    if hashlib.sha256((source/'project/RESEARCH_BRIEF.md').read_bytes()).hexdigest() != BRIEF_SHA:
        raise ValueError('formal resume brief mismatch')
    if system == 'arbor':
        paths = ['native-logs/run/.coordinator/'+n for n in ('checkpoint.json','messages.jsonl','idea_tree.json')]
    elif system == 'aris-code':
        native_run_id = tag(native_run_id)
        paths = ['project/.aris/runs/'+native_run_id+'.json']
    else:
        raise ValueError('ARIS or Arbor required')
    return {'source_run_id':source_run_id,'native_run_id':native_run_id,
            'receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
            'state_sha256':{p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in paths}}


def stage(ledger, approval, workspace):
    if approval.get('artifact_classification') != 'diagnostic_resumed':
        raise ValueError('resumed formal state must be classified diagnostic_resumed')
    resume = approval['native_resume']
    actual = binding(approval['system'], resume['source_run_id'], resume.get('native_run_id'))
    if actual != resume:
        raise ValueError('archived resume binding mismatch')
    source = workspace_path(ROOT/'offline-verification'/resume['source_run_id'])
    previous = json.loads((ROOT/'admin_review'/resume['source_run_id']/'evidence/parameter-ledger.json').read_text())
    if previous['approved_settings'] != ledger['approved_settings']:
        raise ValueError('resume must preserve approved scientific settings')
    plan = build(ledger, approval['system'], (source/'project/RESEARCH_BRIEF.md').read_text())
    workspace = workspace_path(workspace); workspace.mkdir(mode=0o700)
    for entry in source.iterdir():
        if entry.name == 'venv':
            continue
        target = workspace/entry.name
        if entry.is_symlink(): target.symlink_to(entry.readlink())
        elif entry.is_dir(): shutil.copytree(entry,target,symlinks=True)
        else: shutil.copy2(entry,target)
    if approval['system'] == 'arbor':
        plan['native_argv'][0] += ['--resume','--','--allow-non-base-branch']
    else:
        plan['native_argv'][0][-1] += '\n— resume '+resume['native_run_id']
    plan.update(resume_environment=str(source/'venv'),artifact_classification='diagnostic_resumed')
    (workspace/'formal-resume.json').write_text(json.dumps(resume,indent=2)+'\n')
    return plan
