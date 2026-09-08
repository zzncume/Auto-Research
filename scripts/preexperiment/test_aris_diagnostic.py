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

    def test_compatibility_binary_is_hash_bound_and_preserves_task(self):
        from pathlib import Path
        import tempfile
        from unittest.mock import patch
        import aris_diagnostic
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root/'ai-context-hub/projects/autoresearch/task.md'
            task.parent.mkdir(parents=True); task.write_text('CPU fixture')
            binary = root/'tools/aris-code-v0.4.24/reviewer-timeout-compat/aris'
            binary.parent.mkdir(parents=True); binary.write_bytes(b'offline fixture')
            approval = dict(system='aris-code', use_gpu=False,
                            task_path='projects/autoresearch/task.md',
                            task_sha256=hashlib.sha256(task.read_bytes()).hexdigest(),
                            native_options=dict(AUTO_WRITE=True, CODE_REVIEW=True, BASE_REPO=False, VENUE='CVPR'),
                            reviewer_timeout_compatibility=dict(timeout_seconds=1200,
                                binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
            with patch.object(aris_diagnostic, 'ROOT', root), patch.object(aris_diagnostic, 'workspace_path', side_effect=lambda p:p):
                result = aris_diagnostic.stage(approval, root/'work')
                self.assertEqual(result['native_argv'][0][:3], ['env', 'ARIS_REVIEWER_TIMEOUT_SECONDS=1200', '/tools/reviewer-timeout-compat/aris'])
                self.assertEqual((root/'work/project/RESEARCH_BRIEF.md').read_bytes(), task.read_bytes())
                binary.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'binary mismatch'):
                    aris_diagnostic.stage(approval, root/'other')
