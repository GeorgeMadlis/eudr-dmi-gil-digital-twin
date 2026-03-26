#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from aoi_report_renderer import load_report, render_aoi_run, update_evidence_hashes, write_report


def resolve_report_path(run_dir: Path, report_json_name: str | None) -> Path:
    if report_json_name:
        report_path = run_dir / report_json_name
        if report_path.is_file():
            return report_path
        raise SystemExit(f"Report JSON not found: {report_path}")

    fallback = run_dir / "aoi_report.json"
    if fallback.is_file():
        return fallback

    candidates = sorted(
        path for path in run_dir.glob("*.json") if path.name not in {"summary.json", "manifest.json"}
    )
    if len(candidates) == 1:
        return candidates[0]

    if not candidates:
        raise SystemExit(f"No report JSON found in run dir: {run_dir}")

    names = ", ".join(path.name for path in candidates)
    raise SystemExit(
        f"Multiple JSON candidates found in {run_dir}. Use --report-json-name. Candidates: {names}"
    )


def render_run(run_dir: Path, update_json: bool, report_json_name: str | None) -> None:
    report_path = resolve_report_path(run_dir, report_json_name)
    report = load_report(report_path)

    render_aoi_run(run_dir, report_json_name=report_path.name)

    if update_json:
        updated = update_evidence_hashes(run_dir, report)
        write_report(report_path, updated)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AOI HTML/JSON/CSV from a run report JSON file.")
    parser.add_argument("--run-dir", required=True, help="Path to site/aoi_reports/runs/<run_id>")
    parser.add_argument(
        "--report-json-name",
        default=None,
        help="Custom root report JSON filename (default: auto-detect, preferring aoi_report.json)",
    )
    parser.add_argument("--update-json", action="store_true", help="Update evidence_artifacts hashes and sizes")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise SystemExit(f"Run dir not found: {run_dir}")

    render_run(run_dir, update_json=args.update_json, report_json_name=args.report_json_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
