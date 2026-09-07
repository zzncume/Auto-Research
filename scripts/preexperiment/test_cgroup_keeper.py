import tempfile,unittest
from pathlib import Path
from cgroup_keeper import validate_group,UNIT

class KeeperTests(unittest.TestCase):
    def check(self,members,controllers='cpu memory pids'):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/UNIT;p.mkdir();(p/'cgroup.procs').write_text(members);(p/'cgroup.controllers').write_text(controllers)
            validate_group(p,123)
    def test_synthetic_empty_delegation_valid(self):self.check('123\n')
    def test_refuses_other_process(self):
        with self.assertRaises(ValueError):self.check('123\n456\n')
    def test_refuses_incomplete_controllers(self):
        with self.assertRaises(ValueError):self.check('123\n','cpu memory')

if __name__=='__main__':unittest.main()
