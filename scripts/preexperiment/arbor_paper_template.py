"""Approved paper-format input and read-only final Git artifact check."""
import re
import subprocess

INSTRUCTION = '''Paper format requirement (user-approved): Read /materials/MATERIALS.md.
Write the English paper using the supplied official CVPR 2026 review template.
A writable copy is in /work/project/paper; the reference is /materials/native-latex.
Fill in paper/main.tex and its section files. Preserve the CVPR review style,
two-column layout, letter paper size, margins and fonts; do not substitute a generic
article layout or override it with geometry. Main text is limited to eight pages,
excluding references; put supplementary material separately. Compile the paper PDF.
'''

def check(project, template):
    """Inspect committed files only; never repair or retry the research run."""
    try:
        ref = 'research/run/trunk'
        def git(*args):
            return subprocess.check_output(['git', '-C', str(project), *args], stderr=subprocess.DEVNULL)
        names = git('ls-tree', '-r', '--name-only', ref).decode().splitlines()
        candidates = [n for n in names if n.startswith('paper/') and n.endswith('.tex')]
        entries = []
        for name in candidates:
            raw = git('show', ref+':'+name).decode(errors='replace')
            text = re.sub(r'(?<!\\)%[^\n]*', '', raw)
            if '\\documentclass' not in text:
                continue
            entries.append({'path':name,
                'review_style':bool(re.search(r'\\usepackage\[[^]]*\breview\b[^]]*\]\{cvpr\}', text)),
                'two_column_letter':bool(re.search(r'\\documentclass\[[^]]*twocolumn[^]]*letterpaper[^]]*\]', text)),
                'geometry_override':bool(re.search(r'\\(?:usepackage(?:\[[^]]*\])?\{geometry\}|geometry\{)', text))})
        styles = [n for n in names if n.startswith('paper/') and n.endswith('/cvpr.sty')]
        style_matches = any(git('show',ref+':'+n) == (template/'cvpr.sty').read_bytes() for n in styles)
        pdfs = [n for n in names if n.startswith('paper/') and n.endswith('.pdf')]
        passed = style_matches and bool(pdfs) and any(e['review_style'] and e['two_column_letter'] and not e['geometry_override'] for e in entries)
        return {'status':'structural_pass' if passed else 'format_failed', 'entries':entries,
                'official_style_unchanged':style_matches, 'pdf_paths':pdfs,
                'limitations':'Structural check only; page limit, rendered layout and correspondence of PDF to source require review.',
                'automatic_repair':False}
    except Exception as exc:
        return {'status':'unverified', 'error_type':type(exc).__name__, 'automatic_repair':False}
