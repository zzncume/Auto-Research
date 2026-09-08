import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import staged_offline as staged
from prepare_inputs import ROOT


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'offline-verification')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.ledger = json.loads((ROOT/'ai-context-hub/projects/autoresearch/parameter-approvals.json').read_text())

    def test_outside_and_symlink_workspaces_denied(self):
        with self.assertRaises(ValueError):
            staged.workspace_path('/tmp/not-a-native-workspace')
        (self.base/'link').symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError):
            staged.workspace_path(self.base/'link/work')

    def test_stage_exclusive_and_no_management_manifest(self):
        work = self.base/'aris'
        staged.stage(self.ledger, 'aris-code', work)
        self.assertEqual(sorted(p.name for p in (work/'project').iterdir()), ['RESEARCH_BRIEF.md'])
        with self.assertRaises(FileExistsError):
            staged.stage(self.ledger, 'aris-code', work)
        argv = staged.command('aris-code', work, ['/tools/aris', '--help'])
        self.assertIn('--unshare-all', argv)
        self.assertIn(str(staged.VIEW/'aris-code'), argv)
        self.assertNotIn(str(staged.VIEW), argv)
        self.assertNotIn(str(staged.VIEW/'ai-scientist-v1'), argv)

    def test_v2_config_drift_denied(self):
        source = self.base/'source'; source.mkdir()
        config = (staged.PROFILES['ai-scientist-v2'][0]/'bfts_config.yaml').read_text()
        (source/'bfts_config.yaml').write_text(config.replace('num_workers: 4', 'num_workers: 9'))
        with patch.dict(staged.PROFILES, {'ai-scientist-v2': (source, None)}):
            with self.assertRaisesRegex(ValueError, 'num_workers'):
                staged.stage(self.ledger, 'ai-scientist-v2', self.base/'v2')

    def test_v1_native_input_symlink_denied(self):
        view = self.base/'view'; selected = view/'ai-scientist-v1'; selected.mkdir(parents=True)
        (selected/'RESEARCH_BRIEF.md').write_bytes((staged.VIEW/'ai-scientist-v1/RESEARCH_BRIEF.md').read_bytes())
        (selected/'unexpected').symlink_to('/tmp')
        with patch.object(staged, 'VIEW', view):
            with self.assertRaisesRegex(ValueError, 'symlink'):
                staged.stage(self.ledger, 'ai-scientist-v1', self.base/'v1')
