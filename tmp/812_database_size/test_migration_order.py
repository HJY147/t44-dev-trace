"""Migration operation order against the committed owner baseline; no database access."""

import importlib.util
import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy.exc import OperationalError
from t44.persistence import delivery, migrations
from t44.persistence.errors import StatementRejected
from t44.persistence.rows import RowsGateway
from t44.persistence.schema import DDL_SHA256, SCHEMA_VERSION


def before(name, tmp_path):
    source = tmp_path / f"before_size_{name}.py"
    source.write_bytes(
        subprocess.check_output(
            [
                "git",
                "show",
                f"935ab5b93bea788672c2b4a088c79cfeed848954:backend/t44/persistence/{name}.py",
            ]
        )
    )
    spec = importlib.util.spec_from_file_location(
        f"t44.persistence.before_size_{name}", source
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def legacy(tmp_path):
    return before("migrations", tmp_path)


class Result:
    def __init__(self, value):
        self.value = value

    def one(self):
        return self.value

    def scalar_one(self):
        return self.value

    def mappings(self):
        return self

    def one_or_none(self):
        return self.value


class Connection:
    def __init__(self, tape, scenario):
        self.tape, self.scenario = tape, scenario

    def __enter__(self):
        self.tape.append(("enter",))
        return self

    def __exit__(self, *args):
        self.tape.append(("exit",))

    def execute(self, statement, parameters=None):
        sql = str(statement)
        self.tape.append(("execute", sql, parameters))
        if sql.startswith("SELECT VERSION"):
            return Result(
                ("8.0.1" if self.scenario == "server" else "8.4.7", "t44_order")
            )
        if "GET_LOCK" in sql:
            return Result(0 if self.scenario == "lock" else 1)
        if "SELECT version" in sql:
            return Result(
                dict(
                    version=SCHEMA_VERSION,
                    ddl_sha256=bytes.fromhex(DDL_SHA256),
                    state=1 if self.scenario == "incomplete" else 2,
                )
            )
        return Result(1)

    def commit(self):
        self.tape.append(("commit",))

    def exec_driver_sql(self, statement):
        self.tape.append(("ddl", statement))
        if self.scenario == "driver" and statement == "CREATE first":
            raise OperationalError(
                statement, {}, RuntimeError(1234, "synthetic driver failure")
            )


def run(module, monkeypatch, scenario):
    tape = []
    connection = Connection(tape, scenario)
    engine = SimpleNamespace(
        dialect=SimpleNamespace(name="mysql"),
        url=SimpleNamespace(database="t44_order"),
        connect=lambda: connection,
    )
    existing = (
        ["t44_schema_migrations"]
        if scenario in ("applied", "incomplete", "applied-drift")
        else []
    )
    if scenario == "nonempty":
        existing = ["foreign_table"]
    monkeypatch.setattr(
        module, "inspect", lambda _: SimpleNamespace(get_table_names=lambda: existing)
    )
    monkeypatch.setattr(
        module, "ddl_text", lambda: "-- comment\nCREATE first; CREATE second;"
    )

    def check(_):
        tape.append(("schema_check",))
        return dict(
            passed=scenario not in ("applied-drift", "created-drift"), defects=[]
        )

    monkeypatch.setattr(module, "check_schema", check)
    try:
        result = module.migrate(engine, expected_database="t44_order")
    except module.MigrationError as error:
        result = ("error", str(error))
    return result, tape


@pytest.mark.parametrize(
    "scenario",
    [
        "applied",
        "fresh",
        "server",
        "lock",
        "incomplete",
        "nonempty",
        "driver",
        "applied-drift",
        "created-drift",
    ],
)
def test_migration_preserves_result_and_order(monkeypatch, legacy, scenario):
    assert run(migrations, monkeypatch, scenario) == run(legacy, monkeypatch, scenario)


def claim(module, monkeypatch, pending, expired, limit):
    tape, serial = [], iter(range(1, 100))
    monkeypatch.setattr(module, "uuid4", lambda: UUID(int=next(serial)))
    gateway = RowsGateway(
        lambda: pytest.fail("No database session allowed"), lambda: None
    )

    def execute(statement, mode, parameters=None):
        compiled = statement.compile()
        tape.append((str(compiled), compiled.params, mode))
        if mode == "rows":
            return [
                dict(id=i, attempts=65535 if i == 1 else i)
                for i in (pending if compiled.params["status_1"] == 1 else expired)[
                    : compiled.params["param_1"]
                ]
            ]
        return 1

    monkeypatch.setattr(gateway, "_execute", execute)

    @contextmanager
    def factory():
        yield SimpleNamespace(gateway=gateway)

    try:
        result = module.OutboxStore(factory).claim(
            now=datetime(2026, 10, 25, tzinfo=UTC), limit=limit
        )
    except (ValueError, StatementRejected) as error:
        result = type(error).__name__, str(error)
    return result, tape


@pytest.mark.parametrize(
    "pending,expired,limit",
    [
        ([1, 2, 3], [4, 5], 2),
        ([1], [2, 3, 4], 3),
        ([], [1, 2], 3),
        ([], [], 3),
        ([1], [2], True),
        ([1], [2], 0),
        ([1], [2], 1.5),
    ],
)
def test_claim_preserves_priority_bounds_fencing_and_sql(
    monkeypatch, tmp_path, pending, expired, limit
):
    legacy = before("delivery", tmp_path)
    assert claim(delivery, monkeypatch, pending, expired, limit) == claim(
        legacy, monkeypatch, pending, expired, limit
    )
