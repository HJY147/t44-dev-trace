"""Render report Mermaid sources using a project-local tool and an existing Chrome."""

import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGURES = {
    "requirements-report": ("context", "use-cases", "states", "blocked"),
    "design-report": ("architecture", "entities", "transaction", "notifications"),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--chrome", type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / "docs/diagrams"
    output.mkdir(parents=True, exist_ok=True)
    temporary = ROOT / ".agent-worktrees/.runtime/diagram-tools"
    config, browser = temporary / "render-config.json", temporary / "browser-config.json"
    config.write_text(json.dumps({
        "theme": "neutral", "securityLevel": "strict",
        "fontFamily": "PingFang SC, Microsoft YaHei, sans-serif",
        "themeVariables": {"fontSize": "16px"},
        "flowchart": {"htmlLabels": False, "curve": "linear"},
    }))
    browser.write_text(json.dumps({"executablePath": str(args.chrome), "headless": True}))
    jobs = []
    for name, names in FIGURES.items():
        source = ROOT / "reports/final" / (name + ".md")
        blocks = re.findall(r"^```mermaid\s*\n(.*?)^```", source.read_text(), re.M | re.S)
        if len(blocks) != len(names):
            raise ValueError(f"Review figure inventory for {name} before rendering")
        for number, (label, block) in enumerate(zip(names, blocks, strict=True), 1):
            stem = f"{name}-{number:02}-{label}"
            mmd = output / (stem + ".mmd")
            mmd.write_text(block.rstrip() + "\n")
            jobs.append((source, mmd, stem))

    def render(job):
        source, mmd, stem = job
        artifacts = {}
        for extension in ("svg", "png"):
            target = output / f"{stem}.{extension}"
            command = [str(args.node), str(args.cli), "-i", str(mmd), "-o", str(target),
                       "-c", str(config), "-p", str(browser), "--no-font-embed", "--size", "2200"]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            (output / f"{stem}-{extension}.log").write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError(f"Rendering failed for {target.name}; retain its raw log")
            artifacts[extension] = {"path": str(target.relative_to(ROOT)), "sha256": digest(target)}
        return {"source": str(source.relative_to(ROOT)), "source_sha256": digest(source),
                "mermaid": str(mmd.relative_to(ROOT)), "mermaid_sha256": digest(mmd),
                "artifacts": artifacts, "visual_inspection": "pending"}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(render, jobs))
    manifest = {"tool": "@mermaid-js/mermaid-cli", "version": "12.0.0",
                "figure_count": len(results), "figures": results}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rendered_figures": len(results), "visual_inspection": "pending"}))


if __name__ == "__main__":
    main()
