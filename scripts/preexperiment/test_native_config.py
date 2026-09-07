import unittest
from pathlib import Path
from native_config import model_environment,arbor_config,aris_argv
from prepare_inputs import ROOT,safe_file

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.brief=(ROOT/'Auto-Research/common_start_package/protocol-v0.9/RESEARCH_BRIEF.md').read_text()
    def test_all_roles(self):
        e=model_environment('aris-code','http://127.0.0.1:18080/v1','offline-placeholder')
        self.assertEqual(e['ARIS_REVIEWER_MODEL'],'qwen3.8-max')
        self.assertEqual(e['ARIS_REVIEWER_PROVIDER'],'custom')
    def test_provider_url_denied(self):
        with self.assertRaises(ValueError):model_environment('arbor','https://example.com/v1','offline')
    def test_full_brief(self):
        a=aris_argv(self.brief,dict(AUTO_WRITE=True,CODE_REVIEW=True,BASE_REPO=False,VENUE='CVPR'))
        self.assertIn(self.brief,a[-1]);self.assertEqual(a[-2],'prompt')
    def test_arbor_meta(self):
        c=arbor_config(self.brief,'http://127.0.0.1:18080/v1','offline')
        self.assertEqual(c['meta_model'],'qwen3.8-max');self.assertEqual(c['task'],self.brief)
        self.assertNotIn('meta_model',c['llm'])
    def test_brief_drift(self):
        with self.assertRaises(ValueError):arbor_config(self.brief+'x','http://127.0.0.1:18080/v1','offline')
    def test_path_escape(self):
        with self.assertRaises(ValueError):safe_file(ROOT,'../outside')

if __name__=='__main__':unittest.main()
