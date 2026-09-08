"""Route native requests-based Semantic Scholar searches to the local gateway.

Only the transport changes: native query fields, results and retry logic remain.
The provider key lives at the trusted gateway, never in this adapter.
"""
from urllib.parse import urlsplit


def install(endpoint, local_token):
    import requests
    endpoint = endpoint.rstrip('/')
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path:
        raise ValueError('local loopback gateway required')
    original = requests.sessions.Session.request

    def request(self, method, url, **kwargs):
        target = urlsplit(url)
        if target.hostname == 'api.semanticscholar.org':
            if method.upper() != 'GET' or target.path != '/graph/v1/paper/search':
                raise ValueError('unsupported native Semantic Scholar operation')
            headers = {k: v for k, v in kwargs.get('headers', {}).items()
                       if k.lower() not in ('x-api-key', 'authorization')}
            headers['Authorization'] = 'Bearer '+local_token
            kwargs['headers'] = headers
            kwargs['allow_redirects'] = False
            url = endpoint+target.path+('?' + target.query if target.query else '')
        return original(self, method, url, **kwargs)

    requests.sessions.Session.request = request
    return original
