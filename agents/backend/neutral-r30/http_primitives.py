"""Owned HTTP primitives copied from the published neutral preparation; no old entrypoint."""

import datetime as dt
import hashlib
import http.client
import json
import os
import ssl
import time
import urllib.parse
import uuid

UTC = dt.timezone.utc


def stamp(value):
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parsed(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def save(path, value):
    with path.open("x") as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def choose_escalations(tasks, excluded, stop, count=10):
    # Level 3 is open-ended; neither current clock nor the whole future window crosses it.
    eligible = [
        t
        for t in tasks
        if t["id"] not in excluded
        and t["state"] in (1, 2, 3, 4, 5)
        and parsed(t["plan"]["planned_end"]) < stop - dt.timedelta(days=1, minutes=1)
    ]
    eligible.sort(key=lambda row: row["id"])
    if len(eligible) < count:
        raise ValueError("INSUFFICIENT_DISJOINT_STABLE_LEVEL3_TASKS")
    return eligible[:count]


class Client:
    def __init__(self, origin, ca, output, deadline):
        target = urllib.parse.urlsplit(origin)
        if target.scheme != "https" or target.path not in ("", "/") or target.username:
            raise ValueError("EXPLICIT_HTTPS_ORIGIN_REQUIRED")
        self.target, self.ca, self.output, self.deadline = target, ca, output, deadline
        self.number = 0
        self.connection = None

    def request(self, path, token=None, body=None, method=None):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("NEUTRAL_PREPARATION_DEADLINE")
        self.number += 1
        identifier = f"{uuid.uuid4()}"
        method = method or ("POST" if body is not None else "GET")
        headers = {"Accept": "application/json", "X-Request-ID": identifier}
        if token:
            headers["Authorization"] = "Bearer " + token
        payload = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        if payload is not None:
            headers["Content-Type"] = "application/json"
            headers["Idempotency-Key"] = identifier
        # Credentials are never copied into command lines, public logs or request evidence.
        record = {
            "request_id": identifier,
            "path": path,
            "method": method,
            "started_at": stamp(dt.datetime.now(UTC)),
        }
        try:
            if self.connection is None:
                self.connection = http.client.HTTPSConnection(
                    self.target.hostname,
                    self.target.port or 443,
                    timeout=min(20, left),
                    context=ssl.create_default_context(cafile=str(self.ca)),
                )
            self.connection.timeout = min(20, left)
            self.connection.request(method, "/api/v1" + path, body=payload, headers=headers)
            response = self.connection.getresponse()
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("RESPONSE_SIZE_CAP")
            record.update(
                status=response.status,
                response_bytes=len(raw),
                response_sha256=hashlib.sha256(raw).hexdigest(),
            )
            result = json.loads(raw)
            # Full successful non-login data stays private, preserving 0/null.
            if path != "/auth/login":
                record["response"] = result
            if response.status not in (200, 201, 202) or "data" not in result:
                raise ValueError("REAL_HTTP_PREPARATION_REJECTED")
            return result["data"]
        except Exception as error:
            record["failure_type"] = type(error).__name__
            raise
        finally:
            record["finished_at"] = stamp(dt.datetime.now(UTC))
            save(self.output / (identifier + ".private.json"), record)

    def close(self):
        if self.connection:
            self.connection.close()


def all_pages(client, path, token):
    result, page = [], 1
    while True:
        separator = "&" if "?" in path else "?"
        row = client.request(path + separator + f"page={page}&page_size=100", token)
        result.extend(row["items"])
        if len(result) == row["total"]:
            return result
        if not row["items"] or len(result) > row["total"] or page > 1000:
            raise ValueError("INCONSISTENT_FINITE_PAGE")
        page += 1
