#!/usr/bin/env python3
"""Operator-only static readiness check. Never launches a process or experiment.

Attestations must come from a separately trusted operator ledger. Their external
state hash is mandatory, and receipts are bound to the current protocol and
input/environment/launch snapshots. Presence alone is not evidence of success.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'Auto-Research/protocol/process-run-v1.yaml'

def sha(data): return hashlib.sha256(data).hexdigest()
def valid_hash(value): return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def check(state_file=None,expected_state_sha256=None,root=ROOT,protocol_file=PROTOCOL):
    missing=[]
    try:
        protocol_bytes=protocol_file.read_bytes(); p=json.loads(protocol_bytes)
        if p.get('protocol_id')!='process-run-v1' or p['historical_science']['formal_dependency'] is not False:
            raise ValueError('unexpected_protocol')
        brief=root/p['brief']['path']
        if sha(brief.read_bytes())!=p['brief']['sha256']: missing.append('frozen_brief_hash_mismatch')
        gates=p['required_readiness_evidence']
        state={}
        if state_file is None or not valid_hash(expected_state_sha256):
            missing.append('externally_anchored_operator_state_required')
        else:
            raw=Path(state_file).read_bytes()
            if sha(raw)!=expected_state_sha256: raise ValueError('operator_state_hash_mismatch')
            state=json.loads(raw)
            if state.get('protocol_sha256')!=sha(protocol_bytes): raise ValueError('protocol_binding_mismatch')
            if not all(valid_hash(state.get('bindings',{}).get(k)) for k in ['input','environment','launch']):
                raise ValueError('missing_snapshot_binding')
        for gate in gates:
            item=state.get('gates',{}).get(gate)
            if not isinstance(item,dict) or item.get('status')!='verified':
                missing.append(gate); continue
            receipt=Path(item.get('receipt',''))
            if not receipt.is_absolute() or receipt.is_symlink() or receipt.resolve()!=receipt:
                missing.append(gate+':unsafe_receipt_path'); continue
            raw=receipt.read_bytes()
            if sha(raw)!=item.get('sha256'):
                missing.append(gate+':receipt_hash_mismatch'); continue
            data=json.loads(raw)
            if not (data.get('gate')==gate and data.get('result')=='pass' and data.get('protocol_sha256')==sha(protocol_bytes)
                    and data.get('bindings')==state.get('bindings') and data.get('authority')=='trusted_operator'
                    and data.get('evidence_refs')):
                missing.append(gate+':receipt_not_validated'); continue
            for ref in data['evidence_refs']:
                evidence=Path(ref['path'])
                if not evidence.is_absolute() or evidence.is_symlink() or evidence.resolve()!=evidence or sha(evidence.read_bytes())!=ref['sha256']:
                    missing.append(gate+':evidence_hash_mismatch')
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        missing.append('invalid_or_unreadable_readiness_evidence')
    return {'protocol_id':'process-run-v1','status':'BLOCKED' if missing else 'READY_FOR_FORMAL_RUN_APPROVAL',
            'missing':missing,'launch_performed':False,'reference_builder_required':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path); parser.add_argument('--expected-state-sha256')
    args=parser.parse_args(); result=check(args.state,args.expected_state_sha256)
    print(json.dumps(result,indent=2)); return 0 if not result['missing'] else 2

if __name__=='__main__': raise SystemExit(main())
