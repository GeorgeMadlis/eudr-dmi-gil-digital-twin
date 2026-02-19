#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def resolve_report_json_path(run_dir: Path) -> Path:
    preferred_candidates = sorted(path for path in run_dir.glob("*_aoi_report.json") if path.is_file())
    if len(preferred_candidates) == 1:
        return preferred_candidates[0]
    if len(preferred_candidates) > 1:
        names = ", ".join(path.name for path in preferred_candidates)
        raise SystemExit(f"Multiple *_aoi_report.json candidates in {run_dir}: {names}")

    default = run_dir / "aoi_report.json"
    if default.is_file():
        return default

    candidates = sorted(
        path for path in run_dir.glob("*.json") if path.name not in {"summary.json", "manifest.json"}
    )
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise SystemExit(f"Missing run report JSON in {run_dir}")
    names = ", ".join(path.name for path in candidates)
    raise SystemExit(f"Multiple run report JSON candidates in {run_dir}: {names}")


def validate_run(run_dir: Path) -> None:
    report_path = resolve_report_json_path(run_dir)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    evidence = report.get("evidence_artifacts", [])
    if not evidence:
        raise SystemExit(f"No evidence_artifacts entries in {report_path}")

    missing = []
    html_relpaths = []
    for entry in evidence:
        relpath = entry.get("relpath")
        if not relpath:
            continue
        artifact_path = run_dir / relpath
        if not artifact_path.is_file():
            missing.append(relpath)
        if relpath.endswith(".html"):
            html_relpaths.append(relpath)

    if missing:
        raise SystemExit(f"Missing declared artefacts in {run_dir}: {missing}")

    report_html = run_dir / "report.html"
    if not report_html.is_file():
        raise SystemExit(f"Missing run report.html: {report_html}")

    report_html_text = report_html.read_text(encoding="utf-8")
    for relpath in html_relpaths:
        if relpath not in report_html_text:
            raise SystemExit(
                f"report.html missing link to declared HTML artefact: {relpath}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AOI run artefacts and links.")
    parser.add_argument("--runs-dir", default="docs/site/aoi_reports/runs", help="Runs directory")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.is_dir():
        raise SystemExit(f"Runs directory not found: {runs_dir}")

    for entry in sorted(runs_dir.iterdir()):
        if entry.is_dir():
            validate_run(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
