"""Opt-in Qwen HTTP read timeout adaptation; native requests/retries unchanged."""
import copy
import os


def install():
    value = os.environ.get('AUTORESEARCH_LLM_TIMEOUT_SECONDS')
    if value is None:
        return
    seconds = int(value)
    if not 1 <= seconds <= 3600:
        raise ValueError('LLM timeout must be within the supported 1–3600s range')
    import openai
    for client_class in (openai.OpenAI, openai.AsyncOpenAI):
        original = client_class.__init__
        if getattr(original, '_autoresearch_timeout', False):
            continue
        def init(self, *args, _original=original, **kwargs):
            # Change only the implicit SDK read timeout. Explicit native
            # overrides and connect/write/pool limits retain their semantics.
            if 'timeout' not in kwargs:
                timeout = copy.copy(openai.DEFAULT_TIMEOUT)
                timeout.read = max(timeout.read, seconds) if timeout.read is not None else None
                kwargs['timeout'] = timeout
            _original(self, *args, **kwargs)
        init._autoresearch_timeout = True
        client_class.__init__ = init
    if os.environ.get('AUTORESEARCH_NATIVE_SYSTEM') == 'ai-scientist-v1':
        import aider.models
        aider.models.request_timeout = max(aider.models.request_timeout, seconds)
