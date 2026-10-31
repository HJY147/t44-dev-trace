"""Read-only cold-start connectivity, before any session issuance. No credentials logged."""
import base64
import hashlib
import http.client
import json
import socket
import ssl
import sys
import time
from urllib.parse import urlsplit


def wait_ready(database, https, *, budget=28, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + budget
    attempts = 0
    while clock() < deadline:
        attempts += 1
        try:
            database()
            https()
            if clock() >= deadline:
                break
            return {'status': 'CONNECTIONS_READY', 'attempts': attempts,
                    'session_operations': 0, 'sql': 'SELECT 1',
                    'http': 'OPTIONS /api/v1/projects expected405 AllowPOSTorGET'}
        except Exception:
            pass  # Driver exceptions can contain credentials. Never print them.
        left = deadline - clock()
        if left > 0:
            sleep(min(0.2, left))
    raise RuntimeError('READONLY_CONNECTIONS_NOT_READY')


def database_probe():
    import pymysql
    from t44.settings import Settings
    s = Settings.from_env().mysql_settings()
    with pymysql.connect(host=s.host, port=s.port, user=s.username, password=s.password,
                         database=s.database, connect_timeout=1, read_timeout=1,
                         write_timeout=1) as db, db.cursor() as cursor:
        cursor.execute('SELECT 1')
        if cursor.fetchone() != (1,):
            raise RuntimeError('SELECT1_FAILED')


def validate_router_response(status, allow, body):
    # Starlette reports the first PARTIAL route match's method, not their union.
    # bcec registers POST before GET at this path; either registration order is valid.
    methods = {value.strip() for value in (allow or '').split(',') if value.strip()}
    if status != 405 or not methods or not methods <= {'POST', 'GET'} or len(body) > 65536:
        raise RuntimeError('API_ROUTER_OPTIONS_READBACK_REQUIRED')
    try:
        valid = json.loads(body) == {'detail': 'Method Not Allowed'}
    except (ValueError, UnicodeError):
        valid = False
    if not valid:
        raise RuntimeError('API_ROUTER_OPTIONS_BODY_REQUIRED')


def tls_probe(origin, ca_pem, host='tls-gateway', port=8443):
    target = urlsplit(origin)
    if (target.scheme != 'https' or not target.hostname or target.username or target.password
            or target.path not in ('', '/') or target.query or target.fragment):
        raise ValueError('ORIGINAL_HTTPS_ORIGIN_REQUIRED')
    context = ssl.create_default_context(cadata=ca_pem)
    # Preserve original SNI/certificate/Host while routing to the existing TLS gateway.
    class Connection(http.client.HTTPSConnection):
        def connect(self):
            raw = socket.create_connection((host, port), timeout=1)
            try:
                self.sock = context.wrap_socket(raw, server_hostname=target.hostname)
            except BaseException:
                raw.close()
                raise
    conn = Connection(target.hostname, target.port or 443, timeout=1, context=context)
    try:
        conn.request('OPTIONS', '/api/v1/projects', headers={'Host': target.netloc})
        response = conn.getresponse()
        body = response.read(65537)
        validate_router_response(response.status, response.getheader('Allow'), body)
    finally:
        conn.close()


def main():
    value = json.load(sys.stdin)
    ca = base64.b64decode(value['ca_b64'], validate=True)
    if hashlib.sha256(ca).hexdigest() != value['ca_sha256']:
        raise ValueError('ORIGINAL_CA_SHA_REQUIRED')
    try:
        result = wait_ready(database_probe, lambda: tls_probe(value['origin'], ca.decode()))
    except Exception:
        print(json.dumps({'status': 'CONNECTIONS_NOT_READY', 'session_operations': 0}))
        raise SystemExit(1) from None
    print(json.dumps(result))


if __name__ == '__main__':
    main()
