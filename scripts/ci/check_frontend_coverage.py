"""Require real Vitest results and coverage of all executable TS/Vue sources."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    folder = ROOT / "frontend/coverage"
    result = json.loads((folder / "test-results.json").read_text())
    if not result.get("success") or result.get("numPassedTests", 0) <= 0 or result.get("numPendingTests", 0):
        raise ValueError("frontend tests failed, were empty, or contained skipped placeholders")
    report = json.loads((folder / "coverage-final.json").read_text())
    measured = {Path(name).resolve() if Path(name).is_absolute() else (ROOT / "frontend" / name).resolve() for name in report}
    required = {path.resolve() for path in (ROOT / "frontend/src").rglob("*")
                if path.suffix in {".ts", ".vue"} and not path.name.endswith(".d.ts")}
    if not required or required - measured:
        raise ValueError(f"frontend production files absent from coverage: {sorted(str(p.relative_to(ROOT)) for p in required - measured)}")
    totals = json.loads((folder / "coverage-summary.json").read_text())["total"]
    print(json.dumps({metric: totals[metric] for metric in ["statements", "branches", "functions", "lines"]}, indent=2))
    lines = totals["lines"]
    if lines["total"] <= 0 or lines["covered"] * 100 < lines["total"] * 80:
        raise ValueError("frontend line coverage is below 80%")
    print("Frontend real tests and complete TS/Vue line coverage passed. Declaration-only .d.ts excluded; branches/functions reported.")


if __name__ == "__main__":
    main()
