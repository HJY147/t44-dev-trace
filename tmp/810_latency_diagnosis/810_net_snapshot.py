"""Explicit Linux read-only TCP/FD interval counts, no addresses, payload or kernel writes."""

import argparse
import json
import os
import platform
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


def parse_ss(output, port, ephemeral):
    states, api_states, ports = Counter(), Counter(), set()
    recvq = sendq = invalid = listen_recvq = listen_sendq = 0
    for line in output.splitlines():
        fields = line.split()
        try:
            state, receive, send = fields[0], int(fields[1]), int(fields[2])
            local, peer = (
                int(p) if p.isdigit() else None
                for p in (fields[3].rsplit(":", 1)[1], fields[4].rsplit(":", 1)[1])
            )
        except (IndexError, ValueError):
            invalid += 1
            continue
        states[state] += 1
        if state != "LISTEN":
            recvq += receive
            sendq += send
        if local == port or peer == port:
            api_states[state] += 1
            if state == "LISTEN":
                listen_recvq += receive
                listen_sendq += send
        if local is not None and ephemeral[0] <= local <= ephemeral[1]:
            ports.add(local)
    return {
        "tcp_states": dict(states),
        "api_port_states": dict(api_states),
        "distinct_local_ephemeral_ports": len(ports),
        "recvq_bytes_sum_non_listen": recvq,
        "sendq_bytes_sum_non_listen": sendq,
        "api_listen_reported_queue_sums": {"recvq": listen_recvq, "sendq": listen_sendq},
        "unparsed_lines": invalid,
        "port_count_is_not_exhaustion_proof": True,
    }


def protocol_counters(path, prefixes):
    lines = Path(path).read_text().splitlines()
    values = {}
    for first, second in zip(lines[::2], lines[1::2], strict=False):
        headers, numbers = first.split(), second.split()
        if headers and numbers and headers[0] == numbers[0] and headers[0] in prefixes:
            values[headers[0]] = {
                key: int(value)
                for key, value in zip(headers[1:], numbers[1:], strict=True)
                if key
                in {
                    "ActiveOpens",
                    "PassiveOpens",
                    "AttemptFails",
                    "EstabResets",
                    "CurrEstab",
                    "RetransSegs",
                    "InErrs",
                    "OutRsts",
                    "ListenOverflows",
                    "ListenDrops",
                    "TCPTimeouts",
                    "TCPAbortOnTimeout",
                    "TCPAbortOnMemory",
                    "TCPMemoryPressures",
                }
            }
    return values


def snapshot(pids, port, identities):
    row = {"utc": datetime.now(UTC).isoformat(), "monotonic_ns": time.perf_counter_ns()}
    start = time.perf_counter_ns()
    try:
        ephemeral = tuple(
            map(int, Path("/proc/sys/net/ipv4/ip_local_port_range").read_text().split())
        )
        row["ephemeral_port_range"] = ephemeral
        result = subprocess.run(["ss", "-Htan"], capture_output=True, text=True, timeout=3)
        row["ss_returncode"] = result.returncode
        if result.returncode == 0:
            row["sockets"] = parse_ss(result.stdout, port, ephemeral)
        row["tcp"] = protocol_counters("/proc/net/snmp", {"Tcp:"})
        row["tcp_ext"] = protocol_counters("/proc/net/netstat", {"TcpExt:"})
        row["sockstat"] = {
            fields[0].rstrip(":"): {fields[i]: int(fields[i + 1]) for i in range(1, len(fields), 2)}
            for fields in (
                line.split() for line in Path("/proc/net/sockstat").read_text().splitlines()
            )
        }
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        row["network_observer_error_class"] = type(error).__name__
    row["processes"] = []
    for pid in pids:
        item = {"pid": pid}
        try:
            stat = Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()
            identity = int(stat[19])
            expected = identities.setdefault(pid, identity)
            item.update(start_ticks=identity, identity_stable=identity == expected)
            item["fd_count"] = (
                sum(1 for _ in Path(f"/proc/{pid}/fd").iterdir()) if identity == expected else None
            )
        except (OSError, ValueError, IndexError) as error:
            item.update(fd_count=None, observer_error_class=type(error).__name__)
        row["processes"].append(item)
    row["sampling_wall_ns"] = time.perf_counter_ns() - start
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--pid", type=int, action="append", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--seconds", type=int, choices=range(1, 121), required=True)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run or platform.system() != "Linux" or not 1 <= args.port <= 65535:
        parser.error("Explicit Linux execution and valid new diagnostic port required")
    if not 0.25 <= args.interval <= 5 or any(pid <= 0 for pid in args.pid):
        parser.error("Positive explicit owned PIDs and interval0.25..5 required")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    start, count, identities, complete = time.perf_counter(), 0, {}, False
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
                    "kind": "network_start",
                    "planned_seconds": args.seconds,
                    "interval_seconds": args.interval,
                    "scope": "current Linux network namespace; explicit PIDs only",
                    "not_exhaustion_or_root_cause_proof": True,
                    "sysctls_or_protocol_modified": False,
                }
            )
            + "\n"
        )
        try:
            while True:
                row = snapshot(args.pid, args.port, identities)
                stream.write(json.dumps({"kind": "network_sample", **row}) + "\n")
                stream.flush()
                count += 1
                if time.perf_counter() - start >= args.seconds:
                    complete = True
                    break
                time.sleep(
                    max(
                        0,
                        min(start + count * args.interval, start + args.seconds)
                        - time.perf_counter(),
                    )
                )
        finally:
            stream.write(
                json.dumps(
                    {
                        "kind": "network_final",
                        "samples": count,
                        "elapsed_seconds": time.perf_counter() - start,
                        "collected_to_deadline": complete,
                        "coverage_note": "Check actual sample gaps and null/error rows; one later snapshot is not a full interval",
                    }
                )
                + "\n"
            )


if __name__ == "__main__":
    main()
