"""Apply only explicitly selected per-run compatibility settings in Python children."""
import os
if os.environ.get('AUTORESEARCH_NATIVE_SYSTEM') in ('ai-scientist-v1', 'ai-scientist-v2'):
    from llm_timeout_compat import install
    install()
