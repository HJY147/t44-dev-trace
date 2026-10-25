"""Short-window source935 developer HTTP diagnostic; never formal acceptance."""

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import math
import os
import ssl
import stat
import sys
import threading
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

PRODUCT = "935ab5b93bea788672c2b4a088c79cfeed848954"
DATABASE = "t44c_r9diag935_p"
EVIDENCE = [
    {"kind": 2, "locator": "diagnostic/801", "description": "Synthetic diagnosis"}
]


def utc():
    return datetime.now(UTC).isoformat()


class InvalidDiagnostic(Exception):
    pass


def private_json(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_mode & 0o077
            or info.st_uid != os.geteuid()
        ):
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


def target(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or parsed.hostname != "172.21.182.245"
        or parsed.port != 18445
    ):
        raise InvalidDiagnostic(
            "Only the explicit new diagnostic TLS target is admitted"
        )
    return parsed


class Client:
    def __init__(self, url, ca, timeout=15):
        self.parsed = target(url)
        self.context = ssl.create_default_context(cafile=ca)
        self.timeout = timeout
        self.connection = None
        self.connects = self.connect_ns = self.requests = 0
        self.last = None

    def call(self, path, token=None, body=None, key=None, sample=True):
        self.last = {"utc_start": utc(), "monotonic_start_ns": time.perf_counter_ns()}
        start, cpu = time.perf_counter_ns(), time.thread_time_ns()
        try:
            if self.connection is None:
                connection = http.client.HTTPSConnection(
                    self.parsed.hostname,
                    self.parsed.port,
                    timeout=self.timeout,
                    context=self.context,
                )
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
            raw = (
                None
                if body is None
                else json.dumps(body, separators=(",", ":")).encode()
            )
            if raw is not None:
                headers["Content-Type"] = "application/json"
            self.connection.request(
                "GET" if raw is None else "POST", path, raw, headers
            )
            response = self.connection.getresponse()
            content = response.read(2 * 1048576 + 1)
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
            self.last.update(
                utc_end=utc(), wall_ns=end - start, caller_thread_cpu_ns=end_cpu - cpu
            )

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
    if (
        packet.get("kind") != "source935-development-only"
        or packet.get("product") != PRODUCT
    ):
        raise InvalidDiagnostic("Wrong diagnostic product packet")
    if packet.get("database") != DATABASE:
        raise InvalidDiagnostic("Wrong diagnostic database")
    target(packet["url"])
    expires = [
        datetime.fromisoformat(value["expires_at"])
        for value in packet["sessions"].values()
    ]
    if any(value <= datetime.now(UTC) for value in expires):
        raise InvalidDiagnostic("Session expired")
    slots = packet["slots"]
    ids = [slot[k]["id"] for slot in slots for k in ("transition", "escalation")]
    if not 1 <= len(slots) <= 400 or len(ids) != len(set(ids)):
        raise InvalidDiagnostic("Task assignment is not disjoint")


def worker(index, slot, packet, ca, barrier, deadline, cycles):
    client, rows = Client(packet["url"], ca), []
    task, escalation = slot["transition"], slot["escalation"]
    sessions = packet["sessions"]
    token = sessions[slot["transition_role"]]["access_token"]
    try:
        barrier.wait(timeout=20)
        for _ in range(cycles):
            for operation in (
                "getTask",
                "validateContractPayload",
                "transitionTask",
                "createEscalation",
            ):
                if time.perf_counter() >= deadline[0]:
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
                        expected = (
                            task["blocked_from_state"] if task["state"] == 3 else 3
                        )
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
                            raise InvalidDiagnostic(
                                "Existing event deduplication not observed"
                            )
                    rows.append({"operation": operation, **client.last})
                except Exception as error:
                    rows.append(
                        {
                            "operation": operation,
                            **(client.last or {}),
                            "failure": type(error).__name__,
                        }
                    )
                    return {"client": index, "rows": rows, "failed": True, "slot": slot}
        return {"client": index, "rows": rows, "slot": slot}
    except Exception as error:
        return {
            "client": index,
            "rows": rows,
            "failed": True,
            "failure": type(error).__name__,
            "slot": slot,
        }
    finally:
        client.close()
        slot["transport"] = {
            "connections_established": client.connects,
            "tcp_tls_connect_ns": client.connect_ns,
            "requests_with_response": client.requests,
        }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--updated-packet", required=True)
    parser.add_argument("--clients", type=int, choices=(1, 20, 40, 400), required=True)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument("--seconds", type=int, default=45)
    args = parser.parse_args(argv)
    packet = private_json(args.packet)
    check_packet(packet)
    if (
        not 1 <= args.cycles <= 20
        or not 1 <= args.seconds <= 120
        or len(packet["slots"]) < args.clients
    ):
        raise InvalidDiagnostic("Explicit bounded diagnostic parameters required")
    output, updated = reserve(args.output), None
    try:
        updated = reserve(args.updated_packet)
        barrier, deadline = threading.Barrier(args.clients + 1), [None]
        started = utc()
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.clients
        ) as executor:
            futures = [
                executor.submit(
                    worker,
                    i,
                    packet["slots"][i],
                    packet,
                    args.ca,
                    barrier,
                    deadline,
                    args.cycles,
                )
                for i in range(args.clients)
            ]
            deadline[0] = time.perf_counter() + args.seconds
            barrier.wait(timeout=20)
            released = utc()
            results = [future.result() for future in futures]
        packet["updated_at"] = utc()
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
            "deadline_clients": sum(
                bool(result.get("deadline_reached")) for result in results
            ),
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
        return 1 if report["failed_clients"] else 0
    finally:
        os.close(output)
        if updated is not None:
            os.close(updated)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"diagnostic_failed": type(error).__name__}), file=sys.stderr)
        sys.exit(1)
