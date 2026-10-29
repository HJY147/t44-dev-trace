"""Reviewer-only exact-source and local transcript probes; no external services."""

import ast
import copy
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import types
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.exc import OperationalError
from t44.services.common import Call
from t44.services.errors import Rejected

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "a92e5e73da93ba23748c3bab113103036c395d50"
BACKEND = "41a111f270e949326202b8af5770db8aa7102e82"
DATABASE = "8f29030756139061341e0a636c8774ca790964bd"
BACKEND_FINAL = "a13f74f1021e67ea5cb35c2b69ab94f5651bca79"
CLOC = ROOT.parent / ".runtime/cloc-2.10.pl"
REVIEW = "backend/t44/services/reviews.py"
MIGRATION = "backend/t44/persistence/migrations.py"
RESULT = {"base": BASE, "backend": BACKEND, "database": DATABASE, "checks": []}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def source(ref, path):
    return git("show", f"{ref}:{path}").decode()


def checked(label, value):
    assert value, label
    RESULT["checks"].append(label)


def dump(tree):
    return ast.dump(tree, include_attributes=False)


def load(ref, path, name):
    module = types.ModuleType(name)
    module.__package__ = name.rsplit(".", 1)[0]
    exec(compile(source(ref, path), f"{ref}/{path}", "exec"), module.__dict__)
    return module


old_tree = ast.parse(source(BASE, REVIEW))
new_tree = ast.parse(source(BACKEND, REVIEW))
review_class = next(node for node in new_tree.body if isinstance(node, ast.ClassDef))
helper = next(node for node in review_class.body if node.name == "_latest_assessments")
checked("helper exact arguments and single return", [x.arg for x in helper.args.args] == ["self", "g", "task_id"] and len(helper.body) == 1 and isinstance(helper.body[0], ast.Return))
review_class.body.remove(helper)


class Inline(ast.NodeTransformer):
    count = 0

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "self" and node.func.attr == "_latest_assessments":
            assert len(node.args) == 2 and not node.keywords
            self.count += 1
            replacement = copy.deepcopy(helper.body[0].value)

            class Substitute(ast.NodeTransformer):
                def visit_Name(self, name):
                    return copy.deepcopy(dict(g=node.args[0], task_id=node.args[1]).get(name.id, name))

            return Substitute().visit(replacement)
        return self.generic_visit(node)


inline = Inline()
checked("backend complete module AST equal after two exact helper expansions", dump(inline.visit(new_tree)) == dump(old_tree) and inline.count == 2)

before_ast = ast.parse(source(BASE, MIGRATION))
after_ast = ast.parse(source(DATABASE, MIGRATION))
function = next(node for node in after_ast.body if isinstance(node, ast.FunctionDef) and node.name == "_catalog_defects")
assignment = next(node for node in function.body if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "queries")
mapping = assignment.value
checked("catalog four unique labels retain insertion order", isinstance(mapping, ast.Dict) and [key.value for key in mapping.keys] == ["table_options", "column_options", "index_options", "check_enforcement"])
assignment.value = ast.Tuple(elts=[ast.Tuple(elts=[key, *value.elts], ctx=ast.Load()) for key, value in zip(mapping.keys, mapping.values, strict=True)], ctx=ast.Load())
connection = next(node for node in function.body if isinstance(node, ast.With))
loop = connection.body[0]
checked("catalog item iteration exact static registration", dump(loop.iter) == dump(ast.parse("queries.items()", mode="eval").body) and dump(loop.target) == dump(ast.parse("for label, (query, expected) in x: pass").body[0].target))
loop.target = ast.parse("for label, query, expected in x: pass").body[0].target
loop.iter = ast.Name(id="queries", ctx=ast.Load())
checked("database complete module AST equal after exact registration normalization", dump(before_ast) == dump(after_ast))

for ref, allowed in [(BACKEND, {REVIEW}), (DATABASE, {MIGRATION})]:
    changed = set(git("diff", "--name-only", BASE, ref, "--", "backend/t44", "frontend/src", "frontend/index.html").decode().splitlines())
    checked(f"{ref[:8]} exact product path boundary", changed == allowed)
    checked(f"{ref[:8]} frozen contracts specs and original tests unchanged", not git("diff", "--name-only", BASE, ref, "--", "specs", "records/spec-freezes", "backend/pyproject.toml", "backend/requirements.lock", "tmp/backend", "tmp/frontend", "tmp/ci", ".github/workflows"))
checked("backend final handoff adds no product or original test change", not git("diff", "--name-only", BACKEND, BACKEND_FINAL, "--", "backend", "frontend", "specs", "records/spec-freezes", "tmp"))


class Gateway:
    def __init__(self, latest, fail):
        self.trace, self.latest, self.fail = [], latest, fail
        self.task = dict(id=21, project_id=7, version=3, state=5, schedule_version=2, delivery_cycle=1)
        self.assessment = dict(id=31, project_id=7, task_id=21, version=1, status=1, created_by=8, schedule_version=2, delivery_cycle=1, rollback_plan_version=9)

    def get(self, table, identifier, **options):
        self.trace.append(("get", table, identifier, options))
        if table == "release_assessments" and identifier == 40:
            return copy.deepcopy(self.inserted)
        return copy.deepcopy(self.task if table == "tasks" else self.assessment)

    def rows(self, table, where, **options):
        self.trace.append(("rows", table, where, options))
        if table == "project_members":
            return [] if self.fail == "member" else [dict(user_id=8, active=1)]
        if self.fail == "query":
            raise RuntimeError("query failed")
        return copy.deepcopy(self.latest)

    def insert(self, table, values):
        self.trace.append(("insert", table, copy.deepcopy(values)))
        self.inserted = dict(id=40, version=1, **values)
        return 40

    def update(self, table, where, values):
        self.trace.append(("update", table, copy.deepcopy(where), copy.deepcopy(values)))
        record = self.task if table == "tasks" else self.assessment
        if record["version"] != where["version"]:
            return 0
        record.update(values)
        return 1


def review_run(module, operation, scenario):
    g = Gateway([], scenario)
    g.latest = [] if scenario == "empty" else [copy.deepcopy(g.assessment)]
    call = Call(operation, "reviewer-local", None, path=dict(project_id=7, task_id=21, assessment_id=31))
    call.actor = {"actor_id": 8 if scenario == "self" else 9}
    call.membership = {"roles_mask": 2 if scenario == "role" else 5}
    call.clock = datetime(2026, 10, 29, tzinfo=UTC)
    call.body = dict(expected_version=2 if scenario == "task_version" else 3, expected_assessment_version=2 if scenario == "assessment_version" else 1, risks=[dict(perspective=i) for i in (1, 2, 3, 4)], rollback_plan={"responsible_user_id": 8}, verdict=2 if scenario == "reject" else 1, reason="Reviewer synthetic", evidence=[])
    if scenario == "state":
        g.task["state"] = 4
    if scenario == "risks":
        call.body["risks"] = []
    if scenario == "status":
        g.assessment["status"] = 2
    if scenario == "stale":
        g.latest[0]["id"] = 32
    if scenario == "baseline":
        g.assessment["delivery_cycle"] = 2
    module.model = lambda name, row: (name, copy.deepcopy(row))
    module.task_model = copy.deepcopy
    try:
        outcome = ("return", getattr(module.Reviews(), operation)(g, call))
    except Rejected as error:
        outcome = (type(error).__name__, error.code, error.status, error.current_version)
    except (IndexError, RuntimeError) as error:
        outcome = (type(error).__name__, str(error))
    return dict(outcome=outcome, trace=g.trace, task=g.task, assessment=g.assessment, before=call.before, after=call.after)


old_reviews = load(BASE, REVIEW, "t44.services._r29b_before")
new_reviews = load(BACKEND, REVIEW, "t44.services._r29b_after")
review_results = []
for operation, scenarios in [("createReleaseAssessment", ["ok", "empty", "role", "state", "risks", "member", "query", "task_version"]), ("reviewReleaseAssessment", ["ok", "reject", "empty", "role", "self", "state", "status", "stale", "baseline", "query", "assessment_version", "task_version"])]:
    for scenario in scenarios:
        before, after = review_run(old_reviews, operation, scenario), review_run(new_reviews, operation, scenario)
        checked(f"backend transcript {operation}/{scenario}", before == after)
        expected = dict(role="ACTION_FORBIDDEN", state="STATE_CONFLICT", risks="PARAMETER_INVALID", member="RESOURCE_NOT_FOUND", self="ACTION_FORBIDDEN", status="STATE_CONFLICT", stale="ASSESSMENT_BASELINE_MISMATCH", baseline="ASSESSMENT_BASELINE_MISMATCH", assessment_version="VERSION_CONFLICT", task_version="VERSION_CONFLICT").get(scenario)
        actual = after["outcome"]
        if expected:
            checked(f"backend expected rejection {operation}/{scenario}", actual[:2] == ("Rejected", expected))
        elif scenario == "query":
            checked(f"backend query exception propagated {operation}", actual == ("RuntimeError", "query failed"))
        elif operation == "reviewReleaseAssessment" and scenario == "empty":
            checked("backend original empty list IndexError preserved", actual[0] == "IndexError")
        else:
            checked(f"backend expected success {operation}/{scenario}", actual[0] == "return")
            if operation == "createReleaseAssessment":
                created = actual[1]["assessment"][1]
                checked(f"backend exact created assessment version {scenario}", created["id"] == 40 and created["rollback_plan_version"] == (1 if scenario == "empty" else 10))
        review_results.append(dict(operation=operation, scenario=scenario, **after))
RESULT["backend_transcripts"] = review_results

old_migrations = load(BASE, MIGRATION, "t44.persistence._r29b_before")
new_migrations = load(DATABASE, MIGRATION, "t44.persistence._r29b_after")
checked("catalog actual frozen metadata shared without changed schema source", old_migrations.TABLES is new_migrations.TABLES and len(new_migrations.TABLES) == 18 and sum(len(table.c) for table in new_migrations.TABLES.values()) == 226)


def catalog_run(module, scenario, fail_at):
    events = []

    class Engine:
        @contextmanager
        def connect(self):
            # Capture computed expectations to compare the full actual metadata as well as SQL.
            import inspect

            caller = inspect.currentframe().f_back.f_back
            registration = caller.f_locals["queries"]
            entries = list((label, query, expected) for label, (query, expected) in registration.items()) if isinstance(registration, dict) else list(registration)
            self.entries = entries
            events.append(("enter", copy.deepcopy(entries)))
            try:
                yield self
            finally:
                events.append(("exit",))

        def exec_driver_sql(self, query):
            events.append(("sql", query))
            if sum(event[0] == "sql" for event in events) == fail_at:
                raise OperationalError(query, {}, RuntimeError("reviewer catalog failure"))
            expected = next(expected for label, sql, expected in self.entries if sql == query)
            rows = [(*key, *value) for key, value in expected.items()]
            if scenario == "missing":
                return []
            if scenario == "changed":
                return [(*row[:-1], "reviewer-changed") for row in rows]
            if scenario == "duplicate":
                rows.append((*rows[0][:-1], "reviewer-duplicate"))
            return rows

    try:
        outcome = module._catalog_defects(Engine())
    except OperationalError as error:
        outcome = (type(error).__name__, error.statement, str(error.orig))
    return dict(outcome=outcome, events=events)


catalog_results = []
for scenario, fail_at in [("clean", None), ("missing", None), ("changed", None), ("duplicate", None), *(("clean", i) for i in range(1, 5))]:
    before, after = catalog_run(old_migrations, scenario, fail_at), catalog_run(new_migrations, scenario, fail_at)
    checked(f"catalog full metadata SQL result and context {scenario}/{fail_at}", before == after)
    checked(f"catalog context exits {scenario}/{fail_at}", after["events"][-1] == ("exit",))
    if scenario == "clean" and fail_at is None:
        checked("catalog clean output empty", after["outcome"] == [])
    catalog_results.append(dict(scenario=scenario, fail_at=fail_at, defect_count=len(after["outcome"]) if isinstance(after["outcome"], list) else None, outcome=after["outcome"], sql=[event[1] for event in after["events"] if event[0] == "sql"], metadata_counts=[(label, len(expected)) for label, query, expected in after["events"][0][1]]))
RESULT["catalog_transcripts"] = catalog_results

checked("cloc tool pinned hash", hashlib.sha256(CLOC.read_bytes()).hexdigest() == "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83")
counts = {}
with tempfile.TemporaryDirectory(prefix="cloc-", dir=HERE) as temp:
    snapshot = Path(temp)
    names = [name for name in git("ls-tree", "-r", "--name-only", BASE, "--", "backend/t44", "frontend/src", "frontend/index.html").decode().splitlines() if Path(name).suffix in {".py", ".ts", ".vue", ".css", ".html"}]
    with tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", BASE, "--", *names))) as archive:
        archive.extractall(snapshot, filter="data")
    listing = snapshot / "application.list"
    listing.write_text("\n".join(str(snapshot / name) for name in names) + "\n")
    for label, overrides in [("baseline", {}), ("backend_only", {REVIEW: BACKEND}), ("database_only", {MIGRATION: DATABASE}), ("combined_projection_only", {REVIEW: BACKEND, MIGRATION: DATABASE})]:
        for path in [REVIEW, MIGRATION]:
            (snapshot / path).write_text(source(overrides.get(path, BASE), path))
        command = ["/usr/bin/perl", str(CLOC), "--quiet", "--json", "--by-file", "--list-file=" + str(listing)]
        count = json.loads(subprocess.check_output(command))
        counts[label] = dict(application=count["SUM"]["code"], files=len(names), reviews=count[str(snapshot / REVIEW)]["code"], migrations=count[str(snapshot / MIGRATION)]["code"])
RESULT["pinned_cloc_application_recount"] = counts
checked("actual independent candidate reductions exactly three and four", counts["baseline"]["application"] - counts["backend_only"]["application"] == 3 and counts["baseline"]["application"] - counts["database_only"]["application"] == 4)
RESULT["limitations"] = ["Local exact-source stubs only; serialization is isolated in backend trace checks", "Catalog metadata-derived rows compare transformations, not actual MySQL behavior", "No full CI, real database, RabbitMQ, HTTP, cloud, performance, or independent acceptance", "Combined count is uncommitted byte-level projection; root has not integrated here"]
(HERE / "result.json").write_text(json.dumps(RESULT, ensure_ascii=False, indent=2, default=str) + "\n")
print(json.dumps(dict(checks=len(RESULT["checks"]), backend_scenarios=len(review_results), catalog_scenarios=len(catalog_results), counts=counts), ensure_ascii=False))
