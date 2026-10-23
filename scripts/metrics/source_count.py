"""Count committed source with pinned cloc; never count uncommitted work or dependencies."""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTENSIONS = {".py", ".ts", ".vue", ".css", ".html"}
TOOL_HASH = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def classify(name):
    path = Path(name)
    if name.startswith(("backend/t44/", "frontend/src/")) or name == "frontend/index.html":
        return "application" if path.suffix in EXTENSIONS else None
    if name.startswith(("tmp/backend/", "tmp/frontend/", "tmp/ci/", "tmp/deployment/")):
        return "tests" if path.suffix in EXTENSIONS else None
    if name.startswith(("deployment/", "scripts/ci/")):
        return "deployment_ci" if path.suffix in EXTENSIONS else None
    if name == "specs/database/schema.sql":
        return "schema"
    if name == "specs/contracts/openapi.json" or name.startswith("backend/t44/resources/"):
        return "contracts_rules" if path.suffix == ".json" else None
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cloc", type=Path, default=ROOT / ".agent-worktrees/.runtime/cloc-2.10.pl")
    parser.add_argument("--output", type=Path, default=ROOT / "records/metrics/source-count.json")
    parser.add_argument("--require-range", action="store_true")
    args = parser.parse_args()
    if hashlib.sha256(args.cloc.read_bytes()).hexdigest() != TOOL_HASH:
        raise SystemExit("cloc differs from the verified v2.10 release asset")
    head = git("rev-parse", "HEAD").decode().strip()
    roots = ["backend/t44", "frontend/src", "frontend/index.html", "tmp/backend",
             "tmp/frontend", "tmp/ci", "tmp/deployment", "deployment", "scripts/ci", "specs/database/schema.sql",
             "specs/contracts/openapi.json"]
    tracked = git("ls-tree", "-r", "--name-only", head, "--", *roots).decode().splitlines()
    groups = {}
    for name in tracked:
        group = classify(name)
        if group:
            groups.setdefault(group, []).append(name)
    runtime = ROOT / ".agent-worktrees/.runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory(prefix="source-count-", dir=runtime) as temporary:
        snapshot = Path(temporary)
        selected = sorted({name for names in groups.values() for name in names})
        archive = git("archive", "--format=tar", head, "--", *selected)
        with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
            contents.extractall(snapshot, filter="data")
        for group, names in groups.items():
            listing, output = snapshot / f"{group}.list", snapshot / f"{group}.json"
            listing.write_text("\n".join(str(snapshot / name) for name in names) + "\n")
            subprocess.run(["/usr/bin/perl", str(args.cloc.absolute()), "--quiet", "--json",
                            "--by-file", "--list-file=" + str(listing),
                            "--report-file=" + str(output)], check=True, capture_output=True)
            data = json.loads(output.read_text())
            results[group] = {
                "summary": data["SUM"],
                "files": {str(Path(key).relative_to(snapshot)): value
                          for key, value in data.items() if key not in {"header", "SUM"}},
            }
    code = results.get("application", {}).get("summary", {}).get("code", 0)
    report = {"commit": head, "tool": "cloc 2.10", "tool_sha256": TOOL_HASH,
              "metric": "physical nonblank noncomment committed application source lines",
              "range": [3500, 5100], "within_range": 3500 <= code <= 5100,
              "groups": results,
              "limitations": ["cloc treats Python docstrings as comments, including runtime multiline strings",
                              "Vue embedded languages use cloc's Vue file counter",
                              "DDL, configuration, tests and operational tooling are separate",
                              "Package copies of OpenAPI/DDL and generated/vendor files are excluded"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"commit": head, "application_code": code,
                      "within_range": report["within_range"],
                      "report": str(args.output)}, ensure_ascii=False))
    return int(args.require_range and not report["within_range"])


if __name__ == "__main__":
    raise SystemExit(main())
