"""Support inline native bibliographies and the frozen CVPR external .bib file."""
from pathlib import Path
import re

INLINE=r'\\begin\{filecontents\}\{references.bib\}(.*?)\\end\{filecontents\}'

def bib_path(tex,folder):
    match=re.search(r'\\bibliography\{([^},]+)\}',tex)
    if not match:raise ValueError('bibliography not declared')
    root=Path(folder).resolve();p=(root/(match.group(1)+'.bib')).resolve()
    if root not in p.parents:raise ValueError('bibliography outside paper directory')
    return p

def bibliography_text(tex,folder):
    match=re.search(INLINE,tex,re.DOTALL)
    return match.group(1) if match else bib_path(tex,folder).read_text()

def append_bibliography(tex,folder,addition):
    if re.search(INLINE,tex,re.DOTALL):
        return tex.replace(r'\end{filecontents}',addition+'\n'+r'\end{filecontents}',1)
    with bib_path(tex,folder).open('a') as f:f.write('\n'+addition+'\n')
    return tex
