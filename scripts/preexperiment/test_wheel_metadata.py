import os,tempfile,unittest
from pathlib import Path
from repair_wheel_tags import atomic_write

class WheelMetadataTest(unittest.TestCase):
    def test_repair_does_not_mutate_hardlinked_package_cache(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cache=root/'cache';installed=root/'installed'
            cache.write_bytes(b'upstream metadata');os.link(cache,installed)
            atomic_write(installed,b'corrected metadata')
            self.assertEqual(cache.read_bytes(),b'upstream metadata')
            self.assertEqual(installed.read_bytes(),b'corrected metadata')
            self.assertNotEqual(cache.stat().st_ino,installed.stat().st_ino)

if __name__=='__main__':unittest.main()
