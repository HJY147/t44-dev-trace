"""Pure Core-expression candidate; never open an engine or issue an HTTP call."""

import argparse
import ast
import difflib
import hashlib
import inspect
import json
import os
import signal
import socket
import statistics
import tempfile
import textwrap
import time
from pathlib import Path

from diagnose import SOURCE, export_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    if args.output.parent.resolve() != root / "agents/backend/cpu-profile-20261028":
        raise ValueError("ROLE_OUTPUT_ONLY")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    report = {
        "source": SOURCE,
        "status": "started",
        "HTTP_calls": 0,
        "DB_connections": 0,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "formal_acceptance": False,
    }

    def denied(*args, **kwargs):
        raise RuntimeError("NETWORK_FORBIDDEN")

    def expired(*args):
        raise TimeoutError("PURE_45_SECOND_CAP")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = denied
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(45)
    try:
        with tempfile.TemporaryDirectory(prefix="t44-a12-expression-") as temporary:
            import sys

            exported = Path(temporary)
            report["source_manifest"] = export_source(root, exported)
            sys.path.insert(0, str(exported / "backend"))
            from sqlalchemy.dialects import mysql, sqlite
            from t44.persistence import rows
            from t44.persistence.schema import TABLES

            original = rows.RowsGateway.rows
            source = textwrap.dedent(inspect.getsource(original))
            if source.count("tuple(t.c)") != 1:
                raise ValueError("EXACT_SINGLE_EXPRESSION_REQUIRED")
            changed = source.replace("tuple(t.c)", "(t,)")
            new_ast = ast.parse(changed)

            # A structural proof: substitute precisely the one source AST node and compare everything else.
            class Replace(ast.NodeTransformer):
                def visit_Call(self, node):
                    if ast.unparse(node) == "tuple(t.c)":
                        return ast.parse("(t,)", mode="eval").body
                    return self.generic_visit(node)

            if ast.dump(Replace().visit(ast.parse(source)), include_attributes=False) != ast.dump(
                new_ast, include_attributes=False
            ):
                raise ValueError("ONE_NODE_AST_PROOF_FAILED")
            namespace = dict(rows.__dict__)
            exec(compile(changed, "<candidate-one-expression>", "exec"), namespace)
            candidate = namespace["rows"]

            class Capture(rows.RowsGateway):
                def __init__(self):
                    super().__init__(denied, denied)

                def _execute(self, statement, mode, parameters=None):
                    return statement

            gateway = Capture()
            dialects = (mysql.dialect(), sqlite.dialect())

            def signature(function, table, where, options, dialect):
                try:
                    statement = function(gateway, table, where, **options)
                    compiled = statement.compile(dialect=dialect, compile_kwargs={"render_postcompile": True})
                    return (
                        "ok",
                        str(compiled),
                        compiled.params,
                        [(c.key, type(c.type).__name__) for c in statement.selected_columns],
                        [(c.keyname, c.name, type(c.type).__name__) for c in compiled._result_columns],
                    )
                except Exception as error:
                    return ("error", type(error).__name__, str(error))

            cases = []
            for name in TABLES:
                cases += [
                    (name, {"id": 1}, {}),
                    (name, {"id": [1, 2]}, {"limit": 1, "lock": "share"}),
                    (name, {"id": []}, {"limit": 0, "lock": "update", "skip_locked": True}),
                    (name, {"id": 2}, {"columns": ("id",), "order_by": ("-id",), "offset": 3, "limit": 7}),
                    (name, {}, {"predicates": (rows.Pred("id", "ge", 1),), "limit": 4}),
                ]
            cases += [
                ("not_a_table", {}, {}),
                ("tasks", {"not_a_field": 1}, {}),
                ("tasks", {"id": 1}, {"columns": ("not_a_field",)}),
                ("tasks", {"id": 1}, {"order_by": ("not_a_field",)}),
                ("tasks", {"id": 1}, {"limit": True}),
                ("tasks", {"id": 1}, {"offset": -1}),
                ("tasks", {"id": 1}, {"lock": "invalid"}),
                ("tasks", {"id": 1}, {"skip_locked": True}),
                ("tasks", {}, {"predicates": (rows.Pred("id", "invalid", 1),)}),
            ]
            report["signature_evidence"] = []
            for case_index, (table, where, options) in enumerate(cases):
                for dialect in dialects:
                    a = signature(original, table, where, options, dialect)
                    b = signature(candidate, table, where, options, dialect)
                    if a != b:
                        raise ValueError("SQL_PARAMS_COLUMNS_OR_REJECTION_DIFFERED")
                    report["signature_evidence"].append(
                        {
                            "case": case_index,
                            "table": table,
                            "dialect": dialect.name,
                            "where_keys": list(where),
                            "options": {k: repr(v) for k, v in options.items()},
                            "equal": True,
                            "original": a,
                            "candidate": b,
                        }
                    )
            report["guards"] = {
                "tables": len(TABLES),
                "cases": len(cases),
                "dialects": ["mysql", "sqlite"],
                "signature_pairs_equal": len(cases) * 2,
                "checks": "SQL text, bound params, selected column key/type order, exception class/message",
                "one_source_AST_expression_changed": True,
            }
            plans = [
                (t, {"id": 1}, {"limit": 1}) for t in ("users", "auth_sessions", "project_members", "projects", "tasks")
            ]
            timings = []
            # ABBA construction only; statement execution is intercepted before any Session/Engine.
            for label, function in (("A1", original), ("B1", candidate), ("B2", candidate), ("A2", original)):
                samples = []
                for _ in range(5):
                    before = time.thread_time_ns()
                    for _ in range(20):
                        for table, where, options in plans:
                            function(gateway, table, where, **options)
                    samples.append((time.thread_time_ns() - before) / 1000 / 100)
                timings.append(
                    {
                        "phase": label,
                        "statements": 500,
                        "batch_mean_us_per_statement": samples,
                        "median_batch_mean_us_per_statement": statistics.median(samples),
                    }
                )
            report.update(
                status="completed",
                timings=timings,
                statement_construction_only=True,
                candidate_diff="".join(
                    difflib.unified_diff(
                        source.splitlines(True),
                        changed.splitlines(True),
                        fromfile="a12 RowsGateway.rows",
                        tofile="temporary prototype",
                    )
                ),
                production_changes=0,
                expected_net_effective_line_change=0,
                original_function_sha256=hashlib.sha256(source.encode()).hexdigest(),
                candidate_function_sha256=hashlib.sha256(changed.encode()).hexdigest(),
            )
    except BaseException as error:
        report.update(status="failed", failure_class=type(error).__name__)
        raise
    finally:
        signal.alarm(0)
        with os.fdopen(fd, "w") as output:
            output.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "signature_pairs_equal": report["guards"]["signature_pairs_equal"],
                "timings": report["timings"],
            }
        )
    )


if __name__ == "__main__":
    main()
