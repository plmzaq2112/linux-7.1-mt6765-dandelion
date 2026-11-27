import socket, threading, select
from urllib.parse import urlsplit

LISTEN = ('0.0.0.0', 3128)
UPSTREAM = ('127.0.0.1', 10808)
LOG = lambda *a: print(*a, flush=True)


def pipe(a, b):
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 60)
            if not r:
                continue
            for s in r:
                data = s.recv(65536)
                if not data:
                    return
                (b if s is a else a).sendall(data)
    except Exception:
        pass


def handle(conn):
    upstream = None
    try:
        conn.settimeout(30)
        data = b''
        while b'\r\n\r\n' not in data:
            chunk = conn.recv(4096)
            if not chunk:
                return
            data += chunk
            if len(data) > 65536:
                return
        head, _, rest = data.partition(b'\r\n\r\n')
        lines = head.split(b'\r\n')
        method, target, version = lines[0].split(b' ', 2)

        upstream = socket.create_connection(UPSTREAM, 10)

        if method == b'CONNECT':
            LOG('CONNECT', target.decode())
            upstream.sendall(b'CONNECT ' + target + b' HTTP/1.1\r\nHost: ' + target + b'\r\n\r\n')
            resp = b''
            while b'\r\n\r\n' not in resp:
                chunk = upstream.recv(4096)
                if not chunk:
                    break
                resp += chunk
            rhead, _, rrest = resp.partition(b'\r\n\r\n')
            conn.sendall(rhead + b'\r\n\r\n')
            if rrest:
                conn.sendall(rrest)
        else:
            LOG('GET', target.decode())
            upstream.sendall(head + b'\r\n\r\n' + rest)

        pipe(conn, upstream)
    except Exception as e:
        LOG('ERR', type(e).__name__, e)
        try:
            conn.sendall(b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n')
        except Exception:
            pass
    finally:
        for s in (upstream, conn):
            try:
                s.close()
            except Exception:
                pass


srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(LISTEN)
srv.listen(64)
LOG('proxy (upstream 127.0.0.1:10808) listening on', LISTEN)
while True:
    c, a = srv.accept()
    threading.Thread(target=handle, args=(c,), daemon=True).start()
