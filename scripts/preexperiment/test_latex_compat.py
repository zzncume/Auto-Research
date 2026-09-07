import tempfile
from pathlib import Path
import unittest
from latex_compat import bibliography_text,append_bibliography

class TestBib(unittest.TestCase):
    def test_external_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'main.bib').write_text('@article{old}')
            tex=r'\bibliography{main}'
            self.assertEqual(bibliography_text(tex,p),'@article{old}')
            self.assertEqual(append_bibliography(tex,p,'@article{new}'),tex)
            self.assertIn('@article{old}',(p/'main.bib').read_text())
            self.assertIn('@article{new}',(p/'main.bib').read_text())
    def test_inline(self):
        tex=r'\begin{filecontents}{references.bib}old\end{filecontents}'
        self.assertEqual(bibliography_text(tex,'.'),'old')
        self.assertIn('new',append_bibliography(tex,'.','new'))
    def test_escape(self):
        with self.assertRaises(ValueError):bibliography_text(r'\bibliography{../outside}','.')

if __name__=='__main__':unittest.main()
