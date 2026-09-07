import socket
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from local_relay import server

class Echo(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data=self.request.recv(8192)
            if not data:return
            self.request.sendall(data)

class TestRelay(unittest.TestCase):
    def test_unix_bridge(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.sock'
            upstream=socketserver.ThreadingUnixStreamServer(str(p),Echo)
            relay=server(p,0)
            threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in (upstream,relay)]
            for t in threads:t.start()
            try:
                with socket.create_connection(relay.server_address,timeout=5) as c:
                    data=('offline 測試\n'*1000).encode();c.sendall(data);c.shutdown(socket.SHUT_WR)
                    result=b''
                    while True:
                        block=c.recv(8192)
                        if not block:break
                        result+=block
                    self.assertEqual(result,data)
                self.assertEqual(relay.server_address[0],'127.0.0.1')
            finally:
                relay.shutdown();upstream.shutdown();relay.server_close();upstream.server_close()
                for t in threads:t.join(timeout=5)

if __name__=='__main__':unittest.main()
