"""Measure the exact allowed product scope, including deleted files and new helpers."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "e45a2b980c6ba8c61761f897414d54a10000409d"
CLOC = ROOT.parent / ".runtime/cloc-2.10.pl"
EXPECTED = "bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83"
if hashlib.sha256(CLOC.read_bytes()).hexdigest() != EXPECTED:
    raise RuntimeError("Pinned cloc tool mismatch")
files = sorted(
    [
        *ROOT.glob("backend/t44/domain/**/*.py"),
        *ROOT.glob("backend/t44/services/**/*.py"),
        ROOT / "backend/t44/api.py",
        ROOT / "backend/t44/contracts/__init__.py",
    ]
)
baseline_files = [
    ROOT / path
    for path in subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            BASE,
            "--",
            "backend/t44/domain",
            "backend/t44/services",
            "backend/t44/api.py",
            "backend/t44/contracts/__init__.py",
        ],
        cwd=ROOT,
    )
    .decode()
    .splitlines()
    if path.endswith(".py")
]
counts, hashes = {}, {}
with tempfile.TemporaryDirectory(dir=HERE, prefix="cloc-baseline-") as directory:
    for phase in ("before", "after"):
        targets = []
        for file in baseline_files if phase == "before" else files:
            path = file.relative_to(ROOT)
            target = file
            if phase == "before":
                target = Path(directory) / path
                raw = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
                hashes[str(path)] = hashlib.sha256(raw).hexdigest()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            targets.append(target)
        listing = HERE / (phase + ".list")
        listing.write_text("\n".join(map(str, targets)) + "\n")
        output = HERE / (phase + "-cloc.json")
        subprocess.run(
            [
                "/usr/bin/perl",
                str(CLOC),
                "--quiet",
                "--json",
                "--by-file",
                "--list-file=" + str(listing),
                "--report-file=" + str(output),
            ],
            check=True,
            capture_output=True,
        )
        counts[phase] = json.loads(output.read_text())["SUM"]["code"]
(HERE / "baseline-source-hashes.json").write_text(
    json.dumps({"base": BASE, "sha256": hashes}, indent=2) + "\n"
)
print(json.dumps({**counts, "net": counts["before"] - counts["after"]}))
