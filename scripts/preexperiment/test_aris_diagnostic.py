import hashlib
import unittest

from native_config import aris_argv, aris_diagnostic_argv


class DiagnosticBindingTests(unittest.TestCase):
    def test_diagnostic_hash_and_formal_brief_guards_remain_separate(self):
        task = 'Synthetic CPU fixture only.'
        digest = hashlib.sha256(task.encode()).hexdigest()
        options = dict(AUTO_WRITE=True, CODE_REVIEW=True, BASE_REPO=False, VENUE='CVPR')
        with self.assertRaisesRegex(ValueError, 'frozen brief'):
            aris_argv(task, options)
        with self.assertRaisesRegex(ValueError, 'diagnostic task'):
            aris_diagnostic_argv(task+'changed', digest, options)
        argv = aris_diagnostic_argv(task, digest, options)
        self.assertIn(task, argv[-1])
        self.assertEqual(argv[argv.index('--permission-mode')+1], 'danger-full-access')
        self.assertEqual(argv[argv.index('--output-format')+1], 'text')
