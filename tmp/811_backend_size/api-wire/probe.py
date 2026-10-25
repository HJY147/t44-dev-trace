"""Developer-only exact API rendering oracle; never imported by product code."""

import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi.responses import JSONResponse
from t44.contracts import VERSION, violations
from t44.services.common import wire
from t44.services.errors import Rejected

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def rendering_tree(source):
    handle = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "handle"
    )
    index = next(
        index
        for index, node in enumerate(handle.body)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "payload" for target in node.targets)
    )
    arguments = (
        ast.parse(
            "def render(operation,c,status,result,replayed,original,settings,now,time,wire,started): pass"
        )
        .body[0]
        .args
    )
    function = ast.FunctionDef(
        name="render", args=arguments, body=handle.body[index:], decorator_list=[]
    )
    return ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))


def compile_renderer(tree):
    namespace = {
        "JSONResponse": JSONResponse,
        "Rejected": Rejected,
        "VERSION": VERSION,
        "violations": violations,
    }
    exec(compile(tree, "<exact-api-render-tail>", "exec"), namespace)
    return namespace["render"]


def baseline_renderer():
    raw = (HERE / "base-render.py").read_bytes()
    manifest = json.loads((HERE / "base-render-manifest.json").read_text())
    if hashlib.sha256(raw).hexdigest() != manifest["render_sha256"]:
        raise RuntimeError("API rendering oracle changed")
    return compile_renderer(ast.parse(raw))


def candidate_renderer():
    return compile_renderer(rendering_tree((ROOT / "backend/t44/api.py").read_text()))


def render(
    renderer, operation, call, result, settings, *, server_time=None, duration_ms=0, normalize=wire
):
    timestamp = datetime.fromisoformat(server_time) if server_time else datetime.now(UTC)
    return renderer(
        operation,
        call,
        *result,
        settings,
        lambda: timestamp,
        SimpleNamespace(perf_counter=lambda: duration_ms / 1000),
        normalize,
        0.0,
    )


class RestoreNormalization(ast.NodeTransformer):
    def visit_NamedExpr(self, node):
        if isinstance(node.target, ast.Name) and node.target.id == "payload":
            return node.value
        return self.generic_visit(node)

    def visit_Return(self, node):
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "JSONResponse"
            and isinstance(node.value.args[0], ast.Name)
            and node.value.args[0].id == "payload"
        ):
            node.value.args[0] = ast.Call(
                func=ast.Name(id="wire", ctx=ast.Load()), args=node.value.args[:1], keywords=[]
            )
        return self.generic_visit(node)
