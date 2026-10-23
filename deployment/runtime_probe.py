"""Container-local liveness/dependency probe; no new HTTP API or session token."""

import os
import socket
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def check_database() -> None:
    import pymysql

    url = urlsplit(os.environ["DATABASE_URL"])
    if url.scheme != "mysql+pymysql" or not url.path.strip("/"):
        raise ValueError("invalid database configuration")
    with pymysql.connect(
        host=url.hostname,
        port=url.port or 3306,
        user=unquote(url.username or ""),
        password=unquote(url.password or ""),
        database=url.path.lstrip("/"),
        connect_timeout=3,
        read_timeout=3,
        write_timeout=3,
    ) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        if cursor.fetchone() != (1,):
            raise RuntimeError("database probe failed")


def check_process(module: str) -> None:
    for command in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            args = command.read_bytes().split(b"\0")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if any(args[index : index + 2] == [b"-m", module.encode()] for index in range(len(args))):
            return
    raise RuntimeError("worker process is absent")


def main() -> int:
    try:
        role = sys.argv[1]
        if role == "api":
            with socket.create_connection(("127.0.0.1", 8000), timeout=3):
                pass
        elif role in {"consumer", "scheduler"}:
            check_process({"consumer": "t44.messaging", "scheduler": "t44.scheduling"}[role])
        else:
            raise ValueError("unknown probe role")
        check_database()
    except Exception:  # noqa: BLE001 -- fail closed and redact driver-specific connection details
        # Exception text can include a database URL or driver connection details.
        print("local process/dependency check failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
