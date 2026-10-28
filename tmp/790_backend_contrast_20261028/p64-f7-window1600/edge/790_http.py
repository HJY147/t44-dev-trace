"""Short-window exact-source-f7 developer HTTP diagnostic; never formal acceptance."""

import argparse
import concurrent.futures
import hashlib
import http.client
import importlib
import ipaddress
import json
import math
import os
import re
import ssl
import stat
import sys
import threading
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlsplit
from uuid import UUID, uuid4

authority = importlib.import_module("790_authority")

PRODUCT = "f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f"
DATABASE = None
EVIDENCE = [{"kind": 2, "locator": "diagnostic/790", "description": "Synthetic diagnosis"}]


def utc():
    return datetime.now(UTC).isoformat()


class InvalidDiagnostic(Exception):
    pass


class DiagnosticAborted(InvalidDiagnostic):
    pass


def private_json(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.geteuid():
            raise InvalidDiagnostic("Private input ownership/mode invalid")
        with os.fdopen(descriptor, "r") as source:
            descriptor = None
            return json.load(source)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def reserve(path):
    return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)


def write_fd(descriptor, value):
    raw = (json.dumps(value, separators=(",", ":")) + "\n").encode()
    while raw:
        count = os.write(descriptor, raw)
        if count <= 0:
            raise OSError("Output did not progress")
        raw = raw[count:]


CONTROL = None
CONTROL_SHA256 = None
KIND = "t44-contrast-development-v1"
HARDSTOP = datetime(2026, 10, 28, 16, 0, tzinfo=UTC)


def parse_utc(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise InvalidDiagnostic("Explicit UTC required")
    return result


def configure(path, expected):
    global CONTROL, CONTROL_SHA256, DATABASE
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise InvalidDiagnostic("Explicit control hash required")
    value = private_json(path)
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
        raise InvalidDiagnostic("Control hash differs")
    match = re.fullmatch(r"r28p(7|16|64)gen[0-9]{2}", value.get("run_id", ""))
    if (
        not match
        or value.get("kind") != KIND
        or value.get("source_sha") != PRODUCT
        or value.get("database") != "t44c_" + value["run_id"] + "_p"
        or value.get("namespace") != "t44-cloud-" + value["run_id"] + "-p"
        or type(value.get("api_workers")) is not int
        or value["api_workers"] != int(match[1])
        or not re.fullmatch(r"[0-9a-f]{64}", value.get("binding_sha256", ""))
        or not re.fullmatch(r"[0-9a-f]{64}", value.get("ca_sha256", ""))
        or value.get("seed") != 44
        or value.get("anchor_at") != "2026-10-28T04:00:00Z"
        or not datetime.now(UTC) < parse_utc(value["stop_utc"]) <= HARDSTOP
    ):
        raise InvalidDiagnostic("Fresh exact-source bounded contrast control required")
    if CONTROL is not None and dict(CONTROL) != value:
        raise InvalidDiagnostic("Cannot change control inside a running process")
    authority.check_control(value, "pressure", datetime.now(UTC))
    CONTROL, CONTROL_SHA256, DATABASE = MappingProxyType(value), expected, value["database"]
    target(value["url"])


def context_fields():
    if CONTROL is None:
        raise InvalidDiagnostic("Explicit contrast control required")
    return {
        "binding_sha256": CONTROL["binding_sha256"],
        "namespace": CONTROL["namespace"],
        "control_sha256": CONTROL_SHA256,
        "api_workers": CONTROL["api_workers"],
        "stop_utc": CONTROL["stop_utc"],
        "seed": CONTROL["seed"],
        "anchor_at": CONTROL["anchor_at"],
    }


def require_context(value):
    if any(value.get(key) != item for key, item in context_fields().items()):
        raise InvalidDiagnostic("Packet belongs to another arm/binding/control")
    if datetime.now(UTC) >= parse_utc(CONTROL["stop_utc"]):
        raise InvalidDiagnostic("Contrast deadline expired")


def target(url):
    if CONTROL is None:
        raise InvalidDiagnostic("Explicit contrast control required")
    parsed = urlsplit(url)
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError:
        raise InvalidDiagnostic("Private IPv4 TLS endpoint required") from None
    if (
        url.rstrip("/") != CONTROL["url"].rstrip("/")
        or parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or address.version != 4
        or not address.is_private
        or address.is_loopback
        or not port
        or not 1024 <= port <= 65535
        or port == 13306
    ):
        raise InvalidDiagnostic("Only the exact newly bound private TLS target is admitted")
    return parsed


def remaining_timeout(cap, abort=None):
    if abort is not None and abort.is_set():
        raise DiagnosticAborted("Another client failed; no new dispatch")
    if CONTROL is None:
        raise InvalidDiagnostic("Explicit contrast control required")
    remaining = (min(parse_utc(CONTROL["stop_utc"]), HARDSTOP) - datetime.now(UTC)).total_seconds()
    if remaining <= 0:
        raise InvalidDiagnostic("Absolute diagnostic deadline expired")
    return min(cap, remaining)


class Client:
    def __init__(self, url, ca, timeout=15, abort=None):
        self.parsed = target(url)
        self.context = ssl.create_default_context(cafile=ca)
        self.timeout, self.abort = timeout, abort
        self.connection = None
        self.connects = self.connect_ns = self.requests = 0
        self.last = None

    def socket_timeout(self, check_abort=True):
        value = remaining_timeout(self.timeout, self.abort if check_abort else None)
        if self.connection is not None:
            self.connection.timeout = value
            if self.connection.sock is not None:
                self.connection.sock.settimeout(value)
        return value

    def call(self, path, token=None, body=None, key=None, sample=True):
        self.last = {
            "utc_start": utc(),
            "monotonic_start_ns": time.perf_counter_ns(),
            "request_dispatch_attempted": False,
            "body_read_complete": False,
        }
        start, cpu = time.perf_counter_ns(), time.thread_time_ns()
        try:
            remaining_timeout(self.timeout, self.abort)
            if self.connection is None:
                connection = http.client.HTTPSConnection(
                    self.parsed.hostname,
                    self.parsed.port,
                    timeout=remaining_timeout(self.timeout, self.abort),
                    context=self.context,
                )
                self.connection = connection
                connected = time.perf_counter_ns()
                connection.connect()
                self.connect_ns += time.perf_counter_ns() - connected
                self.connects += 1
                self.connection = connection
            headers = {"Accept": "application/json"}
            if token:
                headers["Authorization"] = "Bearer " + token
            if key:
                headers["Idempotency-Key"] = key
            if sample:
                headers["X-T44-Diag-Sample"] = "1"
            raw = None if body is None else json.dumps(body, separators=(",", ":")).encode()
            if raw is not None:
                headers["Content-Type"] = "application/json"
            self.socket_timeout()
            self.last["request_dispatch_attempted"] = True
            self.connection.request("GET" if raw is None else "POST", path, raw, headers)
            self.socket_timeout(check_abort=False)
            response = self.connection.getresponse()
            self.last.update(
                status=response.status,
                response_headers_received=True,
                request_id=response.getheader("X-Request-ID"),
            )
            self.socket_timeout(check_abort=False)
            content = response.read(2 * 1048576 + 1)
            self.last["body_read_complete"] = True
            self.requests += 1
            self.last.update(
                status=response.status,
                response_bytes=len(content),
                request_id=response.getheader("X-Request-ID"),
                server_timing=response.getheader("Server-Timing"),
                connection_will_close=response.will_close,
            )
            if response.will_close:
                self.close()
            if len(content) > 2 * 1048576:
                raise InvalidDiagnostic("Unexpected response size")
            value = json.loads(content)
            if response.status < 200 or response.status >= 300:
                self.last["error_code"] = value.get("code")
                raise InvalidDiagnostic("HTTP request rejected")
            identifier = str(UUID(self.last["request_id"]))
            if value["meta"]["request_id"] != identifier:
                raise InvalidDiagnostic("Request identity mismatch")
            self.last["replayed"] = value["meta"]["replayed"]
            if self.last["replayed"]:
                raise InvalidDiagnostic("Unexpected idempotency replay")
            return value["data"]
        except BaseException as error:
            self.last["exception_class"] = type(error).__name__
            self.close()
            raise
        finally:
            end_cpu, end = time.thread_time_ns(), time.perf_counter_ns()
            self.last.update(utc_end=utc(), wall_ns=end - start, caller_thread_cpu_ns=end_cpu - cpu)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None


def task_path(task):
    return f"/api/v1/projects/{task['project_id']}/tasks/{task['id']}"


def block_body(task):
    common = {"expected_version": task["version"], "evidence": EVIDENCE}
    if task["state"] == 3:
        return {
            **common,
            "action": 3,
            "basis": "Synthetic diagnostic dependency verified",
        }
    return {
        **common,
        "action": 2,
        "reason": "Synthetic diagnostic",
        "responsibility_stage": 2,
    }


def slim(task):
    return {
        key: task[key]
        for key in (
            "id",
            "project_id",
            "state",
            "version",
            "schedule_version",
            "blocked_from_state",
        )
    }


def check_packet(packet):
    require_context(packet)
    if packet.get("kind") != KIND or packet.get("product") != PRODUCT:
        raise InvalidDiagnostic("Wrong diagnostic product packet")
    if packet.get("database") != DATABASE:
        raise InvalidDiagnostic("Wrong diagnostic database")
    if packet.get("resumable") is not True:
        raise InvalidDiagnostic("Failed or unverified packet cannot resume")
    if datetime.fromisoformat(packet["created_at"]) + timedelta(seconds=600) <= datetime.now(UTC):
        raise InvalidDiagnostic("Prepared fixture diagnostic window expired")
    target(packet["url"])
    if set(packet["sessions"]) != {"manager", "developer", "reviewer", "service"}:
        raise InvalidDiagnostic("Four actual role sessions required")
    expires = [datetime.fromisoformat(value["expires_at"]) for value in packet["sessions"].values()]
    if any(value <= datetime.now(UTC) for value in expires):
        raise InvalidDiagnostic("Session expired")
    slots = packet["slots"]
    ids = [slot[k]["id"] for slot in slots for k in ("transition", "escalation")]
    if not 1 <= len(slots) <= 500 or len(ids) != len(set(ids)):
        raise InvalidDiagnostic("Task assignment is not disjoint")


def worker(index, slot, packet, ca, barrier, deadline, cycles, abort):
    client, rows = None, []
    task, escalation = slot["transition"], slot["escalation"]
    sessions = packet["sessions"]
    token = sessions[slot["transition_role"]]["access_token"]
    try:
        client = Client(packet["url"], ca, abort=abort)
        barrier.wait(timeout=20)
        for _ in range(cycles):
            for operation in (
                "getTask",
                "validateContractPayload",
                "transitionTask",
                "createEscalation",
            ):
                if abort.is_set():
                    return {"client": index, "rows": rows, "aborted": True, "slot": slot}
                if time.perf_counter() >= deadline[0] or datetime.now(UTC) >= parse_utc(
                    CONTROL["stop_utc"]
                ):
                    abort.set()
                    return {
                        "client": index,
                        "rows": rows,
                        "deadline_reached": True,
                        "slot": slot,
                    }
                try:
                    if operation == "getTask":
                        result = client.call(task_path(task), token)
                        if slim(result) != task:
                            raise InvalidDiagnostic("Task changed outside this client")
                    elif operation == "validateContractPayload":
                        result = client.call(
                            f"/api/v1/projects/{task['project_id']}/contract-validations",
                            token,
                            {
                                "category": 2,
                                "task_id": task["id"],
                                "payload": block_body(task),
                            },
                        )
                        if result.get("valid") is not True:
                            raise InvalidDiagnostic("Contract validation failed")
                    elif operation == "transitionTask":
                        expected = task["blocked_from_state"] if task["state"] == 3 else 3
                        result = client.call(
                            task_path(task) + "/transitions",
                            token,
                            block_body(task),
                            str(uuid4()),
                        )
                        updated = slim(result["task"])
                        if (
                            updated["version"] != task["version"] + 1
                            or updated["state"] != expected
                        ):
                            raise InvalidDiagnostic("Unexpected transition result")
                        task = slot["transition"] = updated
                    else:
                        body = {
                            "expected_version": escalation["version"],
                            "schedule_version": escalation["schedule_version"],
                            "rule_version": slot["rule_version"],
                            "scan_run_id": slot["scan_run_id"],
                        }
                        result = client.call(
                            "/api/v1/internal"
                            + task_path(escalation).removeprefix("/api/v1")
                            + "/escalations",
                            sessions["service"]["access_token"],
                            body,
                            str(uuid4()),
                        )
                        if (
                            result.get("created") is not False
                            or result["event"]["id"] != slot["event_id"]
                            or result["task_version"] != escalation["version"]
                        ):
                            raise InvalidDiagnostic("Existing event deduplication not observed")
                    rows.append({"operation": operation, **client.last})
                except DiagnosticAborted:
                    rows.append({"operation": operation, **(client.last or {}), "aborted": True})
                    return {"client": index, "rows": rows, "aborted": True, "slot": slot}
                except Exception as error:  # noqa: BLE001 - anonymous per-client failure evidence
                    abort.set()
                    rows.append(
                        {
                            "operation": operation,
                            **(client.last or {}),
                            "failure": type(error).__name__,
                        }
                    )
                    return {"client": index, "rows": rows, "failed": True, "slot": slot}
        return {"client": index, "rows": rows, "slot": slot}
    except Exception as error:  # noqa: BLE001 - anonymous startup/barrier failure evidence
        abort.set()
        barrier.abort()
        return {
            "client": index,
            "rows": rows,
            "failed": True,
            "failure": type(error).__name__,
            "slot": slot,
        }
    finally:
        if client is not None:
            client.close()
        slot["transport"] = {
            "connections_established": client.connects if client else 0,
            "tcp_tls_connect_ns": client.connect_ns if client else 0,
            "requests_with_response": client.requests if client else 0,
        }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--control", required=True)
    parser.add_argument("--control-sha256", required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--slot-offset", type=int, default=0)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--updated-packet", required=True)
    parser.add_argument("--clients", type=int, choices=(1, 20, 40, 400), required=True)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--seconds", type=int, default=45)
    args = parser.parse_args(argv)
    configure(args.control, args.control_sha256)
    if hashlib.sha256(Path(args.packet).read_bytes()).hexdigest() != args.packet_sha256:
        raise InvalidDiagnostic("Explicit private packet hash differs")
    if hashlib.sha256(Path(args.ca).read_bytes()).hexdigest() != CONTROL["ca_sha256"]:
        raise InvalidDiagnostic("Bound CA changed")
    packet = private_json(args.packet)
    check_packet(packet)
    if (
        not 1 <= args.cycles <= 20
        or not 1 <= args.seconds <= 120
        or not 0 <= args.slot_offset <= 500
        or len(packet["slots"]) < args.slot_offset + args.clients
        or (parse_utc(CONTROL["stop_utc"]) - datetime.now(UTC)).total_seconds() < args.seconds + 30
    ):
        raise InvalidDiagnostic("Explicit bounded diagnostic parameters required")
    output, updated = reserve(args.output), None
    try:
        updated = reserve(args.updated_packet)
        barrier, deadline, abort = threading.Barrier(args.clients + 1), [None], threading.Event()
        selected = packet["slots"][args.slot_offset : args.slot_offset + args.clients]
        before = json.loads(
            json.dumps([{k: slot[k] for k in ("transition", "escalation")} for slot in selected])
        )
        started = utc()
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.clients) as executor:
            futures = [
                executor.submit(
                    worker,
                    i,
                    selected[i],
                    packet,
                    args.ca,
                    barrier,
                    deadline,
                    args.cycles,
                    abort,
                )
                for i in range(args.clients)
            ]
            deadline[0] = time.perf_counter() + args.seconds
            try:
                barrier.wait(timeout=20)
            except threading.BrokenBarrierError:
                barrier.abort()
            released = utc()
            results = [future.result() for future in futures]
        packet["updated_at"] = utc()
        complete = not any(
            result.get("failed") or result.get("deadline_reached") or result.get("aborted")
            for result in results
        ) and all(len(result["rows"]) == args.cycles * 4 for result in results)
        packet["resumable"] = complete
        packet["previous_packet_sha256"] = hashlib.sha256(
            Path(args.packet).read_bytes()
        ).hexdigest()
        write_fd(updated, packet)
        rows = [row for result in results for row in result["rows"]]
        summary = {}
        for operation in sorted({row["operation"] for row in rows}):
            values = sorted(
                row["wall_ns"] / 1e6
                for row in rows
                if row["operation"] == operation and "wall_ns" in row
            )
            summary[operation] = {
                "observed": len(values),
                "p50_ms": values[math.ceil(len(values) * 0.5) - 1],
                "p95_ms": values[math.ceil(len(values) * 0.95) - 1],
                "max_ms": max(values),
            }
        report = {
            "kind": "developer-short-window-not-acceptance",
            "product": PRODUCT,
            **context_fields(),
            "slot_offset": args.slot_offset,
            "expected_requests": args.clients * args.cycles * 4,
            "observed_requests": len(rows),
            "diagnostic_complete": complete,
            "entry_versions_sha256": hashlib.sha256(
                json.dumps(before, sort_keys=True).encode()
            ).hexdigest(),
            "exit_versions_sha256": hashlib.sha256(
                json.dumps(
                    [{k: slot[k] for k in ("transition", "escalation")} for slot in selected],
                    sort_keys=True,
                ).encode()
            ).hexdigest(),
            "database": DATABASE,
            "utc_started": started,
            "utc_barrier_released": released,
            "utc_finished": utc(),
            "clients": args.clients,
            "cycles_limit": args.cycles,
            "duration_limit_seconds": args.seconds,
            "connection_mode": "per-client-reuse-no-retry",
            "summary_includes_failures": True,
            "status_counts": dict(Counter(str(row.get("status")) for row in rows)),
            "summary": summary,
            "failed_clients": sum(bool(result.get("failed")) for result in results),
            "aborted_clients": sum(bool(result.get("aborted")) for result in results),
            "shared_abort_set": abort.is_set(),
            "http_dispatch_attempts": sum(
                bool(row.get("request_dispatch_attempted")) for row in rows
            ),
            "deadline_clients": sum(bool(result.get("deadline_reached")) for result in results),
            "results": [
                {key: value for key, value in result.items() if key != "slot"}
                | {"transport": result["slot"].pop("transport", {})}
                for result in results
            ],
        }
        write_start = time.perf_counter_ns()
        write_fd(output, report)
        write_fd(
            output,
            {
                "kind": "writer_final",
                "writer_ns": time.perf_counter_ns() - write_start,
                "durability": "fsync requested after final write",
            },
        )
        os.fsync(output)
        os.fsync(updated)
        return 0 if complete else 1
    finally:
        os.close(output)
        if updated is not None:
            os.close(updated)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # noqa: BLE001 - never print private exception details
        print(json.dumps({"diagnostic_failed": type(error).__name__}), file=sys.stderr)
        sys.exit(1)
