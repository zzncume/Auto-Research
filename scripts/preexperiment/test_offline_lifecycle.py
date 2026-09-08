"""CPU-only synthetic boundary tests; do not launch any research system."""
import json
from pathlib import Path
import tempfile
import unittest

from offline_lifecycle import verify
from offline_wrapper import ROOT


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'offline-verification')
        self.root = Path(self.temp.name)
        self.work = self.root/'work'
        self.work.mkdir()
        self.source = ROOT/'systems-prepared/preexperiment-20260907/offline-probe'

    def tearDown(self):
        self.temp.cleanup()

    def test_boundary_and_failed_output_preserved(self):
        script = '''import os, socket
from pathlib import Path
assert not Path('/home/zf/projects/autoresearch/secrets').exists()
assert not Path('/home/zf/projects/autoresearch/ai-context-hub').exists()
assert not list(Path('/dev').glob('nvidia*'))
assert not any(k.endswith('API_KEY') for k in os.environ)
assert not Path('/etc/systemd/system').exists()
s=socket.socket(); s.settimeout(.1)
assert s.connect_ex(('192.0.2.1',443)) != 0
Path('/work/failed-artifact').write_text('retained')
print('boundary passed', flush=True)
raise SystemExit(7)
'''
        receipt = verify(self.source, self.work, ['/usr/bin/python3', '-c', script], self.root/'evidence')
        self.assertEqual(receipt['exit_code'], 7)
        self.assertEqual((self.work/'failed-artifact').read_text(), 'retained')
        self.assertIn('boundary passed', (self.root/'evidence/stdout').read_text())
        self.assertFalse(receipt['resource_accounting_complete'])
        with self.assertRaises(FileExistsError):
            verify(self.source, self.work, ['/bin/true'], self.root/'evidence')

    def test_timeout_kills_detached_namespace_descendant(self):
        script = '''import os,time
from pathlib import Path
if os.fork()==0:
 os.setsid(); time.sleep(1); Path('/work/escaped').write_text('bad')
else:
 Path('/work/started').write_text('yes'); time.sleep(30)
'''
        receipt = verify(self.source, self.work, ['/usr/bin/python3', '-c', script], self.root/'timeout', timeout=.5)
        self.assertTrue(receipt['timed_out'])
        self.assertTrue((self.work/'started').exists())
        # A second bounded namespace operation gives any escaped child time to write.
        verify(self.source, self.work, ['/bin/sleep', '1.1'], self.root/'after')
        self.assertFalse((self.work/'escaped').exists())

    def test_operator_evidence_cannot_be_child_writable(self):
        with self.assertRaises(ValueError):
            verify(self.source, self.work, ['/bin/true'], self.work/'evidence')


if __name__ == '__main__':
    unittest.main()
