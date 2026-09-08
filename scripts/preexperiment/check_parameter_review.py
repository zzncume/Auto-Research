"""Check the parameter-review dossier, separately from production readiness.

This does not clear check_readiness.py's production gates. It reports them in
every result, including a ready dossier. It never produces an execution permit.
"""
import argparse
import json
from pathlib import Path

from check_readiness import check as check_production
from prepare_inputs import ROOT, digest

DEFERRED = {'production_isolation_e2e', 'native_launch_archive_e2e'}
SYSTEMS = {'ai-scientist-v1', 'ai-scientist-v2', 'arbor', 'aris-code'}


def check(dossier, expected_sha256, production=None):
    production = check_production() if production is None else production
    missing = [g for g in production['missing'] if g not in DEFERRED]
    try:
        dossier = Path(dossier)
        if dossier.resolve() != dossier or digest(dossier) != expected_sha256:
            raise ValueError('dossier binding mismatch')
        plan = json.loads(dossier.read_text())
        if plan['scope'] != 'parameter_review_only' or plan['parameters_frozen'] is not False:
            raise ValueError('invalid review scope')
        if plan['execution_authorized'] is not False or plan['host_changes_authorized'] is not False:
            raise ValueError('unexpected authorization')
        if set(plan['execution_gates_still_required']) != DEFERRED:
            raise ValueError('production gates must remain explicit')
        if set(plan['systems']) != SYSTEMS:
            raise ValueError('incomplete system coverage')
        required = {'native_help_archive', 'regressions', 'input_recheck', 'parameter_choices'}
        if set(plan['evidence']) != required:
            raise ValueError('incomplete review evidence')
        for kind, bundle in plan['evidence'].items():
            if bundle['result'] != 'pass' or not bundle['refs']:
                raise ValueError('missing evidence: '+kind)
            for ref in bundle['refs']:
                path = Path(ref['path'])
                if not path.is_absolute() or path.resolve() != path or digest(path) != ref['sha256']:
                    raise ValueError('evidence changed: '+kind)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        missing.append('invalid_review_dossier_or_evidence')
    return {'status': 'BLOCKED' if missing else 'READY_FOR_PREEXPERIMENT_PARAMETER_APPROVAL',
            'scope': 'parameter_review_only', 'missing': sorted(set(missing)),
            'production_readiness': production['status'],
            'production_missing': production['missing'],
            'parameters_frozen': False, 'execution_authorized': False,
            'host_changes_authorized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dossier', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    result = check(args.dossier, args.expected_sha256)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['missing']))
