"""Read-only source segmentation diagnostic; never replaces the formal application metric."""

import argparse
import ast
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

BASE = "ade5e4c1998b4c2f014afde8c011645c6c5a7412"
CLOC_SHA = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--cloc", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not args.run:
        parser.error("Explicit --run required")
    if hashlib.sha256(args.cloc.read_bytes()).hexdigest() != CLOC_SHA:
        raise ValueError("Pinned cloc mismatch")
    root = Path(__file__).resolve().parents[2]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    fragment_dir = args.output_dir / "fragments"
    fragment_dir.mkdir()
    expected = json.loads(
        (root / "agents/backend/performance-repair-839/source-count.json").read_text()
    )
    names = [name for name in expected["groups"]["application"]["files"] if name.endswith(".py")]
    fragments = {}
    segments = []
    exact_sequences = defaultdict(list)
    files = {}
    for name in names:
        raw = subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=root)
        if raw != (root / name).read_bytes():
            raise ValueError("Source drift")
        text = raw.decode()
        lines = text.splitlines(keepends=True)
        tree = ast.parse(text)
        residual = list(lines)
        functions = [(node.name, node) for node in tree.body if isinstance(node, ast.FunctionDef)]
        for parent in tree.body:
            if isinstance(parent, ast.ClassDef):
                functions.extend(
                    (parent.name + "." + node.name, node)
                    for node in parent.body
                    if isinstance(node, ast.FunctionDef)
                )
        entries = []
        for label, node in functions:
            start = min([node.lineno, *[value.lineno for value in node.decorator_list]])
            code = "".join(lines[start - 1 : node.end_lineno])
            sha = hashlib.sha256(code.encode()).hexdigest()
            fragments[sha] = code
            entry = {
                "file": name,
                "function": label,
                "start": start,
                "end": node.end_lineno,
                "fragment_sha256": sha,
            }
            segments.append(entry)
            entries.append(entry)
            for index in range(start - 1, node.end_lineno):
                residual[index] = "\n"
        code = "".join(residual)
        sha = hashlib.sha256(code.encode()).hexdigest()
        fragments[sha] = code
        module = {"file": name, "function": "<module declarations/imports>", "fragment_sha256": sha}
        segments.append(module)
        entries.append(module)
        files[name] = {
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "formal_code": expected["groups"]["application"]["files"][name]["code"],
            "segments": entries,
        }
        for node in ast.walk(tree):
            for field in ("body", "orelse", "finalbody"):
                body = getattr(node, field, None)
                if not isinstance(body, list) or not all(
                    isinstance(value, ast.stmt) for value in body
                ):
                    continue
                for length in range(3, min(8, len(body)) + 1):
                    for first in range(len(body) - length + 1):
                        sequence = body[first : first + length]
                        signature = ast.dump(
                            ast.Module(body=sequence, type_ignores=[]), include_attributes=False
                        )
                        if sequence[-1].end_lineno - sequence[0].lineno + 1 >= 8:
                            exact_sequences[signature].append(
                                {
                                    "file": name,
                                    "start": sequence[0].lineno,
                                    "end": sequence[-1].end_lineno,
                                    "statements": length,
                                }
                            )
    selected = []
    for sha, code in fragments.items():
        path = fragment_dir / (sha + ".py")
        path.write_text(code)
        selected.append(path)
    listing = args.output_dir / "fragments.list"
    listing.write_text("\n".join(map(str, selected)) + "\n")
    output = args.output_dir / "fragment-cloc.json"
    subprocess.run(
        [
            "/usr/bin/perl",
            str(args.cloc),
            "--quiet",
            "--json",
            "--by-file",
            "--list-file=" + str(listing),
            "--report-file=" + str(output),
        ],
        check=True,
        capture_output=True,
    )
    counts = json.loads(output.read_text())
    for entry in segments:
        path = fragment_dir / (entry["fragment_sha256"] + ".py")
        entry["fragment_code"] = counts.get(str(path), {}).get("code", 0)
    for info in files.values():
        info["segmented_code"] = sum(entry["fragment_code"] for entry in info["segments"])
        info["reconciles_formal_file_code"] = info["segmented_code"] == info["formal_code"]
    clones = []
    for signature, occurrences in exact_sequences.items():
        positions = {(item["file"], item["start"], item["end"]) for item in occurrences}
        if len(positions) > 1:
            clones.append(
                {
                    "signature_sha256": hashlib.sha256(signature.encode()).hexdigest(),
                    "occurrences": occurrences,
                }
            )
    result = {
        "source": BASE,
        "operator": "reviewer AI static cost diagnostic",
        "files": files,
        "backend_formal_code": sum(info["formal_code"] for info in files.values()),
        "file_partition_matches": all(
            info["reconciles_formal_file_code"] for info in files.values()
        ),
        "largest_functions": sorted(
            (entry for entry in segments if not entry["function"].startswith("<")),
            key=lambda item: -item["fragment_code"],
        )[:30],
        "exact_statement_clones": clones,
        "limitations": [
            "Fragment counters are diagnostic; the fixed committed whole-application metric remains unchanged",
            "AST clones preserve literal/name identity; no semantic clone completeness or unavoidable lower bound is claimed",
            "Clone spans overlap and cannot be summed as net savings",
            "No application imports, functional execution, database or HTTP calls",
        ],
    }
    with (args.output_dir / "ledger.json").open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(
        json.dumps({key: result[key] for key in ("backend_formal_code", "file_partition_matches")})
    )
    print(json.dumps({"clone_groups": len(clones), "function_segments": len(segments)}))


if __name__ == "__main__":
    main()
