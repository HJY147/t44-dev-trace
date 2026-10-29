"""PUBLIC generic tool subset. No business workload, SUT source, account, inventory or secret."""
import multiprocessing
import argparse, array, base64, collections, datetime, gzip, hashlib, hmac, http.client, io, ipaddress, json, math, os, platform, queue, re, resource, signal, socket, ssl, stat, struct, subprocess, sys, threading, time, traceback, urllib.parse, uuid, zlib
from pathlib import Path
GIB = 1024 ** 3
N = 400
WARM = 60
STEADY = 600
FRAME = 262144
RESERVE = 3 * 1024 * 1024
MAX_RESPONSE = 1048576
WORKER_STACK_BYTES = 512 * 1024
HERE = Path(__file__).resolve().parent

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')

def epoch(s):
    d = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset() != datetime.timedelta(0):
        raise ValueError('UTC_REQUIRED')
    return d.timestamp()

def canonical(v):
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, v):
    p = Path(p)
    tmp = p.with_suffix('.new')
    tmp.write_bytes(canonical(v) + b'\n')
    tmp.chmod(384)
    os.replace(tmp, p)

def check(ok, msg):
    if not ok:
        raise ValueError(msg)

def durable_save(path, value):
    path = Path(path)
    path.parent.mkdir(mode=448, parents=True, exist_ok=True)
    tmp = path.with_suffix('.new')
    with tmp.open('wb') as f:
        f.write(canonical(value) + b'\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def phase_path(env):
    return Path(env['output_dir']).parent / (env['run_id'] + '.phase.json')

def phase(env, name, count=0, reason=None):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    value = {'schema': '772-v2-stage-v1', 'run_id': env['run_id'], 'status': 'NP_INCOMPLETE' if name not in ('FINISHED', 'NP') else name, 'phase': name, 'utc': utc(), 'monotonic_ns': time.monotonic_ns(), 'clients_started': count, 'threads_active': threading.active_count(), 'rss': usage.ru_maxrss, 'rss_unit': 'KiB' if platform.system() == 'Linux' else 'bytes', 'rlimit_as': list(resource.getrlimit(resource.RLIMIT_AS)), 'thread_stack_bytes_configured': WORKER_STACK_BYTES, 'reason': reason}
    durable_save(phase_path(env), value)

def exception_code(exc):
    text = str(exc).lower()
    if isinstance(exc, ssl.SSLError):
        return 'TLS_CONTEXT_INITIALIZATION_FAILED'
    if isinstance(exc, threading.BrokenBarrierError):
        return 'CLIENT_START_BARRIER_FAILED'
    if isinstance(exc, RuntimeError) and 'start new thread' in text:
        return 'CLIENT_THREAD_START_FAILED'
    if isinstance(exc, MemoryError):
        return 'MEMORY_ALLOCATION_FAILED'
    if isinstance(exc, InterruptedError) and str(exc) == 'OWNED_STOP_SIGNAL':
        return 'OWNED_STOP_SIGNAL'
    return 'HARNESS_' + type(exc).__name__.upper()

def failure_result(env, exc, stage):
    out = Path(env['output_dir'])
    out.mkdir(mode=448, parents=True, exist_ok=True)
    (out / 'failure.private.log').write_text(traceback.format_exc())
    return {'schema': '772-result-v1', 'benchmark': '772-v1', 'runtime_revision': '2.4', 'run_id': env['run_id'], 'utc': utc(), 'metrics_verdict': 'NP', 'full_cohort': False, 'failure_stage': stage, 'failure_code': exception_code(exc), 'exception_type': type(exc).__name__, 'warmup_seconds': 60, 'steady_seconds': 600, 'observed_elapsed_seconds': None, 'classes': {k: {'count': None, 'p95_ms': None} for k in ('query', 'transition', 'contract', 'escalation')}, 'minute_buckets': None, 'failures': {exception_code(exc): 1}, 'postconditions': None, 'independent_conclusion': 'NP_INCOMPLETE_HARNESS_FAILURE', 'raw_evidence_encrypted': (out / 'evidence.772seal').exists(), 'raw_cipher_bytes': (out / 'evidence.772seal').stat().st_size if (out / 'evidence.772seal').exists() else None, 'SUT_requests_observed': None, 'no_retry_or_successor': True}

class Seal:
    """Versioned per-frame encrypt-then-MAC: domain-separated SHAKE256/HMAC-SHA256.
 Keys are 256 random bits, frame nonce=(256-bit salt,64-bit sequence),
 HMAC chains all frame headers and ciphertext. No plaintext/compressed disk copy.
 """
    MAGIC = b'772-SEAL-v1\x00'

    def __init__(self, path, key, cap=12 * GIB):
        self.f = open(path, 'xb', buffering=0)
        self.key = key
        self.salt = os.urandom(32)
        self.seq = 0
        self.count = 0
        self.cap = cap
        self.enc = hmac.digest(key, b'772/enc/' + self.salt, 'sha256')
        self.mac = hmac.digest(key, b'772/mac/' + self.salt, 'sha256')
        self.chain = hmac.digest(self.mac, self.MAGIC + self.salt, 'sha256')
        self._write(self.MAGIC + self.salt + self.chain)

    def _write(self, b):
        check(self.count + len(b) <= self.cap, 'CIPHER_CAP')
        self.f.write(b)
        self.count += len(b)

    def frame(self, payload, kind=1):
        head = struct.pack('>BQI', kind, self.seq, len(payload))
        stream = hashlib.shake_256(self.enc + self.salt + struct.pack('>Q', self.seq)).digest(len(payload))
        cipher = (int.from_bytes(payload, 'big') ^ int.from_bytes(stream, 'big')).to_bytes(len(payload), 'big') if payload else b''
        tag = hmac.digest(self.mac, self.chain + head + cipher, 'sha256')
        self._write(head + cipher + tag)
        self.chain = tag
        self.seq += 1

    def close(self, footer):
        self.frame(canonical(footer), 255)
        self.f.flush()
        os.fsync(self.f.fileno())
        self.f.close()

    @classmethod
    def read(cls, path, key):
        with open(path, 'rb') as f:
            check(f.read(len(cls.MAGIC)) == cls.MAGIC, 'SEAL_MAGIC')
            salt = f.read(32)
            enc = hmac.digest(key, b'772/enc/' + salt, 'sha256')
            mac = hmac.digest(key, b'772/mac/' + salt, 'sha256')
            chain = hmac.digest(mac, cls.MAGIC + salt, 'sha256')
            check(hmac.compare_digest(f.read(32), chain), 'SEAL_HEADER')
            seq = 0
            while True:
                head = f.read(13)
                if not head:
                    return
                check(len(head) == 13, 'SEAL_PARTIAL_HEADER')
                kind, num, size = struct.unpack('>BQI', head)
                check(num == seq and size <= FRAME * 8, 'SEAL_SEQUENCE_OR_SIZE')
                cipher = f.read(size)
                tag = f.read(32)
                check(len(cipher) == size and hmac.compare_digest(tag, hmac.digest(mac, chain + head + cipher, 'sha256')), 'SEAL_AUTH')
                stream = hashlib.shake_256(enc + salt + struct.pack('>Q', seq)).digest(size)
                plain = (int.from_bytes(cipher, 'big') ^ int.from_bytes(stream, 'big')).to_bytes(size, 'big') if size else b''
                yield (kind, plain)
                chain = tag
                seq += 1

class Sink:

    def __init__(self, out, key, limits, stop, queue_slots=800):
        self.out = Path(out)
        self.stop = stop
        self.limits = limits
        self.lock = threading.Lock()
        self.plain = 0
        self.reserved = 0
        self.compressed = 0
        self.reason = None
        self.closed = False
        self.records = 0
        self.block_ns = 0
        self.highwater = 0
        self.last_progress = time.monotonic()
        self.q = queue.Queue(queue_slots)
        self.seal = Seal(self.out / 'evidence.772seal', key, limits['cipher_bytes'])
        self.z = zlib.compressobj(1, zlib.DEFLATED, 31)
        self.thread = threading.Thread(target=self.writer, name='evidence-writer', daemon=True)
        self.thread.start()

    def reserve(self):
        with self.lock:
            if self.reason:
                return False
            if self.plain + self.reserved + RESERVE > self.limits['plain_bytes'] - FRAME or __import__('shutil').disk_usage(self.out).free < 128 * 1024 ** 2 + self.reserved + RESERVE:
                self.fail('CAPACITY_INCOMPLETE')
                return False
            self.reserved += RESERVE
            return True

    def fail(self, why):
        self.reason = self.reason or why
        self.stop.set()

    def put(self, v, reserved=False):
        p = canonical(v) + b'\n'
        start = time.monotonic_ns()
        with self.lock:
            if reserved:
                self.reserved -= RESERVE
            if len(p) > RESERVE or self.plain + self.reserved + len(p) > self.limits['plain_bytes'] - FRAME:
                self.fail('CAPACITY_INCOMPLETE')
                return False
            self.plain += len(p)
            self.records += 1
        while self.thread.is_alive():
            if self.reason is not None:
                return False
            try:
                self.q.put(p, timeout=0.1)
                self.block_ns += time.monotonic_ns() - start
                self.highwater = max(self.highwater, self.q.qsize())
                return True
            except queue.Full:
                if time.monotonic() - self.last_progress >= 5:
                    self.fail('EVIDENCE_WRITER_STALLED')
                    return False
        self.fail('EVIDENCE_WRITER_FAILED')
        return False

    def emit(self, p):
        for offset in range(0, len(p), FRAME):
            part = p[offset:offset + FRAME]
            check(self.compressed + len(part) <= self.limits['compressed_bytes'], 'COMPRESSED_CAP')
            self.seal.frame(part)
            self.compressed += len(part)

    def writer(self):
        try:
            while True:
                p = self.q.get()
                if p is None:
                    break
                self.emit(self.z.compress(p))
                self.last_progress = time.monotonic()
                if self.records % 500 == 0:
                    self.emit(self.z.flush(zlib.Z_SYNC_FLUSH))
            self.emit(self.z.flush(zlib.Z_FINISH))
            self.seal.close({'kind': 'authenticated-prefix', 'records': self.records, 'plain_bytes': self.plain, 'compressed_bytes': self.compressed, 'reason': self.reason, 'utc': utc()})
        except BaseException as e:
            self.fail(type(e).__name__ + ':' + str(e))

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.thread.is_alive():
            try:
                self.q.put(None, timeout=1)
            except queue.Full:
                self.fail('EVIDENCE_WRITER_DRAIN_TIMEOUT')
        self.thread.join(1 if self.reason is not None else 10)
        if self.thread.is_alive():
            self.fail('EVIDENCE_WRITER_DRAIN_TIMEOUT')

class Capture:

    def __init__(self, fp, raw):
        self.fp = fp
        self.raw = raw

    def read(self, n=-1):
        b = self.fp.read(n)
        self.raw.extend(b)
        return b

    def readline(self, n=-1):
        b = self.fp.readline(n)
        self.raw.extend(b)
        return b

    def close(self):
        return self.fp.close()

    def __getattr__(self, k):
        return getattr(self.fp, k)

class Response(http.client.HTTPResponse):

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.raw = bytearray()
        self.fp = Capture(self.fp, self.raw)

class Connection(http.client.HTTPSConnection):
    response_class = Response

    def __init__(self, host, port, ip, context, timeout):
        super().__init__(host, port, timeout=timeout, context=context)
        self.ip = ip
        self.sent = bytearray()

    def connect(self):
        self.sock = socket.create_connection((self.ip, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)

    def send(self, data):
        if isinstance(data, (bytes, bytearray, memoryview)):
            self.sent.extend(data)
        return super().send(data)

def supervise_owned(command, hard_utc, hard_mono, childenv=None, startup_marker=None, startup_timeout=45):
    interrupted = threading.Event()

    def interrupted_handler(signum, frame):
        interrupted.set()
    previous = {s: signal.signal(s, interrupted_handler) for s in (signal.SIGTERM, signal.SIGINT)}
    p = None
    reason = None
    try:
        p = subprocess.Popen(command, env=childenv, start_new_session=True)
        started_mono = time.monotonic()
        running_seen = False
        while p.poll() is None:
            if startup_marker is not None and (not running_seen):
                try:
                    running_seen = json.loads(Path(startup_marker).read_text()).get('phase') in ('RUNNING', 'FINISHED')
                except (OSError, ValueError):
                    pass
                if not running_seen and time.monotonic() - started_mono >= startup_timeout:
                    reason = 'STARTUP_TIMEOUT'
                    break
            if interrupted.is_set():
                reason = 'OPERATOR_STOP'
                break
            if time.time() >= hard_utc or time.monotonic() >= hard_mono:
                reason = 'HARD_DEADLINE'
                break
            time.sleep(0.05)
        if reason:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                p.wait(2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait(2)
        return (p.returncode, reason, p.pid)
    finally:
        if p is not None and p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait(2)
        for signum, handler in previous.items():
            signal.signal(signum, handler)

class Lifecycle:

    def _shutdown_post_pool(self):
        with self.post_pool_lock:
            pool = self.post_pool
            self.post_pool = None
        if pool is not None:
            pool.terminate()
            pool.join()

    def execute(self):
        try:
            value = self._execute()
            self._last_result = value
            return value
        except BaseException as exc:
            self.stop.set()
            try:
                self.barrier.abort()
            except Exception:
                pass
            result = failure_result(self.env, exc, 'STARTUP_OR_EXECUTION_EXCEPTION')
            if self._startup_error is not None:
                result['failure_code'] = self._startup_error
                result['failures'] = {self._startup_error: 1}
            if self.sink is not None and self.sink.reason is None:
                self.sink.put({'record': 'harness_failure', 'utc': utc(), 'reason': result['failure_code'], 'exception_type': type(exc).__name__})
                self.sink.put({'record': 'result', 'result': result})
            self._last_result = result
            save(self.out / 'result.json', result)
            phase(self.env, 'NP', sum((t.ident is not None for t in self.worker_threads)), result['failure_code'])
            return result
        finally:
            self.stop.set()
            try:
                self.barrier.abort()
            except Exception:
                pass
            for connection in self.connections:
                try:
                    if connection.sock:
                        connection.sock.shutdown(socket.SHUT_RDWR)
                    connection.close()
                except Exception:
                    pass
            join_deadline = time.monotonic() + 0.5
            for thread in self.worker_threads:
                if thread.ident is not None:
                    thread.join(max(0, min(0.01, join_deadline - time.monotonic())))
            self._shutdown_post_pool()
            if self.sink is not None:
                self.sink.close()
            if hasattr(self, '_last_result'):
                self._last_result['post_validator_workers'] = 4
                self._last_result['post_validation_jobs'] = self.post_validation_jobs
                self._last_result['post_validator_pool_stopped'] = self.post_pool is None
                self._last_result['raw_cipher_bytes'] = (self.out / 'evidence.772seal').stat().st_size if (self.out / 'evidence.772seal').exists() else None
                self._last_result['writer_finalized'] = bool(self.sink is not None and (not self.sink.thread.is_alive()))
                save(self.out / 'result.json', self._last_result)

def platform_resource_guard():
    check(sys.version_info[:2] == (3, 12), 'PYTHON_3_12_REQUIRED')
    check(platform.system() == 'Linux' and platform.machine() in ('x86_64', 'amd64'), 'LINUX_AMD64_REQUIRED')
    resource.setrlimit(resource.RLIMIT_AS, (8 * GIB, 8 * GIB))
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))
    resource.setrlimit(resource.RLIMIT_NPROC, (2048, 2048))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (8 * 3600, 8 * 3600))
    cpu = Path('/sys/fs/cgroup/cpu.max')
    mem = Path('/sys/fs/cgroup/memory.max')
    pids = Path('/sys/fs/cgroup/pids.max')
    check(cpu.is_file() and mem.is_file() and pids.is_file(), 'CGROUP_V2_LIMITS_REQUIRED')
    quota, period = cpu.read_text().split()
    check(quota != 'max' and int(quota) / int(period) <= 8, 'CPU_CGROUP')
    check(mem.read_text().strip() != 'max' and int(mem.read_text()) <= 8 * GIB, 'MEMORY_CGROUP')
    check(pids.read_text().strip() != 'max' and int(pids.read_text()) <= 2048, 'PIDS_CGROUP')
