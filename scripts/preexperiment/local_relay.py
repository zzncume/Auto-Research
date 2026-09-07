#!/usr/bin/env python3
"""Bridge a private loopback listener to one pre-mounted Unix socket."""
import argparse
import selectors
import socket
import socketserver

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as upstream:
            upstream.settimeout(3600);upstream.connect(self.server.unix_path)
            self.request.settimeout(3600)
            with selectors.DefaultSelector() as events:
                peers={self.request:upstream,upstream:self.request}
                for s in peers:events.register(s,selectors.EVENT_READ)
                while events.get_map():
                    ready=events.select(3600)
                    if not ready:return
                    for key,_ in ready:
                        src=key.fileobj;data=src.recv(65536)
                        if not data:
                            events.unregister(src)
                            try:peers[src].shutdown(socket.SHUT_WR)
                            except OSError:pass
                        else:peers[src].sendall(data)

class Relay(socketserver.ThreadingTCPServer):
    daemon_threads=True
    allow_reuse_address=False

def server(path,port):
    s=Relay(('127.0.0.1',port),Handler);s.unix_path=str(path);return s

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--socket',required=True)
    p.add_argument('--port',type=int,required=True);a=p.parse_args()
    with server(a.socket,a.port) as s:s.serve_forever()
