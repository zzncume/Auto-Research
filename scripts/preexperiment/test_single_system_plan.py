import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

from build_single_system_plan import build, SYSTEMS
from prepare_inputs import ROOT
from single_run_lock import single_run_lock


class SingleSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brief = (ROOT/'Auto-Research/common_start_package/protocol-v0.9/RESEARCH_BRIEF.md').read_text()

    def ledger(self):
        return {'approved_settings': {
            'launch_selection': {'mode': 'user_selected_single_system', 'fixed_order': None,
                                 'max_active_runs': 1, 'auto_start_next': False},
            'whole_run_timeout_seconds': 129600,
            'ai-scientist-v1': {'num_ideas': 5, 'parallel': 0, 'improvement': True},
            'ai-scientist-v2': {'max_num_generations': 1, 'idea_generation_and_reflection_total_rounds': 5,
                                'writeup_max_attempts': 3, 'num_cite_rounds': 20},
            'arbor': {},
            'aris-code': {'AUTO_WRITE': True, 'CODE_REVIEW': True, 'BASE_REPO': False, 'VENUE': 'CVPR'}}}

    def test_each_plan_contains_only_selected_settings_and_never_launches(self):
        for system in SYSTEMS:
            plan = build(self.ledger(), system, self.brief)
            self.assertEqual(plan['system'], system)
            self.assertFalse(plan['execution_authorized'])
            self.assertEqual(plan['processes_started'], 0)
            self.assertNotIn('approved_settings', plan)
            self.assertEqual(plan['whole_run_timeout_seconds'], 129600)

    def test_reject_batch_and_auto_next(self):
        for system in ['all', 'ai-scientist-v1,arbor']:
            with self.assertRaises(ValueError):
                build(self.ledger(), system, self.brief)
        ledger = self.ledger()
        ledger['approved_settings']['launch_selection']['auto_start_next'] = True
        with self.assertRaises(ValueError):
            build(ledger, 'arbor', self.brief)

    def test_v1_approved_idea_count_and_improvement(self):
        argv = build(self.ledger(), 'ai-scientist-v1', self.brief)['native_argv'][0]
        self.assertEqual(argv[argv.index('--num-ideas')+1], '5')
        self.assertIn('--improvement', argv)

    def test_v2_ideation_then_same_system_bfts(self):
        plan = build(self.ledger(), 'ai-scientist-v2', self.brief)
        first, second = plan['native_argv']
        self.assertIn('/engine/ai_scientist/perform_ideation_temp_free.py', first)
        self.assertIn('/engine/launch_scientist_bfts.py', second)
        self.assertIn('&&', plan['shell_preview_inside_future_sandbox'])

    def test_full_brief_survives_shell_preview(self):
        plan = build(self.ledger(), 'aris-code', self.brief)
        self.assertEqual(shlex.split(plan['shell_preview_inside_future_sandbox']), plan['native_argv'][0])
        self.assertIn(self.brief, plan['native_argv'][0][-1])

    def test_lock_rejects_second_process_and_releases_without_unlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'active.lock'
            script = 'from single_run_lock import single_run_lock\nimport sys\nwith single_run_lock(sys.argv[1]): pass\n'
            with single_run_lock(path):
                inode = path.stat().st_ino
                result = subprocess.run([sys.executable, '-B', '-c', script, str(path)],
                                        cwd=Path(__file__).parent, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'another run holds the lock', result.stderr)
            with single_run_lock(path):
                self.assertEqual(path.stat().st_ino, inode)

    def test_lock_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'original'
            target.write_text('unchanged')
            link = Path(tmp)/'link'
            link.symlink_to(target)
            with self.assertRaises(OSError):
                with single_run_lock(link):
                    self.fail('symlink acquired')
            self.assertEqual(target.read_text(), 'unchanged')


if __name__ == '__main__':
    unittest.main()
