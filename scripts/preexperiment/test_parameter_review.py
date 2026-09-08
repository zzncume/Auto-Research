import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from check_parameter_review import check, DEFERRED, SYSTEMS


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence = self.root/'evidence'
        self.evidence.write_text('synthetic offline verification')
        ref = {'path': str(self.evidence), 'sha256': hashlib.sha256(self.evidence.read_bytes()).hexdigest()}
        self.plan = {'scope': 'parameter_review_only', 'parameters_frozen': False,
                     'execution_authorized': False, 'host_changes_authorized': False,
                     'execution_gates_still_required': sorted(DEFERRED), 'systems': sorted(SYSTEMS),
                     'evidence': {k: {'result': 'pass', 'refs': [ref]} for k in
                                  ['native_help_archive', 'regressions', 'input_recheck', 'parameter_choices']}}
        self.production = {'status': 'BLOCKED', 'missing': sorted(DEFERRED)}

    def tearDown(self):
        self.tmp.cleanup()

    def result(self):
        path = self.root/'dossier.json'
        path.write_text(json.dumps(self.plan))
        return check(path, hashlib.sha256(path.read_bytes()).hexdigest(), self.production)

    def test_review_never_clears_production(self):
        r = self.result()
        self.assertEqual(r['status'], 'READY_FOR_PREEXPERIMENT_PARAMETER_APPROVAL')
        self.assertEqual(r['production_missing'], sorted(DEFERRED))
        self.assertEqual(r['production_readiness'], 'BLOCKED')
        self.assertFalse(r['execution_authorized'])

    def test_missing_offline_gate_blocks(self):
        self.production['missing'].append('native_adapters_mock')
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_tampered_evidence_blocks(self):
        self.evidence.write_text('changed')
        self.assertEqual(self.result()['status'], 'BLOCKED')

    def test_implicit_approval_blocks(self):
        for field in ['parameters_frozen', 'execution_authorized', 'host_changes_authorized']:
            self.plan[field] = True
            self.assertEqual(self.result()['status'], 'BLOCKED')
            self.plan[field] = False

    def test_hidden_production_gate_blocks(self):
        self.plan['execution_gates_still_required'] = []
        self.assertEqual(self.result()['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
