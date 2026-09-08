"""Start private relays, then execute one native phase with unchanged argv.

Used inside the isolated child only. Host-side approval/lifecycle owns execution.
"""
import os
import runpy
import subprocess
import sys
import threading

from local_relay import server


def main(argv):
    if not argv:
        raise ValueError('one native phase required')
    relays = []
    for name, port in (('model', 18080), ('literature', 18081), ('egress', 18082)):
        sock = '/transport/'+name+'.sock'
        if os.path.exists(sock):
            relay = server(sock, port)
            thread = threading.Thread(target=relay.serve_forever, daemon=True); thread.start()
            relays.append((relay, thread))
    try:
        if argv[0] == '/env/bin/python':
            from research_transport import install
            if os.path.exists('/transport/literature.sock'):
                install('http://127.0.0.1:18081', os.environ['RESEARCH_LOCAL_TOKEN'])
            if argv[1] == '-m':
                sys.argv = argv[2:]
                runpy.run_module(argv[2], run_name='__main__', alter_sys=True)
            else:
                sys.argv = argv[1:]
                runpy.run_path(argv[1], run_name='__main__')
            return 0
        return subprocess.call(argv)
    finally:
        for relay, thread in relays:
            relay.shutdown(); relay.server_close(); thread.join(5)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
