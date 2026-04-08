#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


SAMPLE_REPORTS_RUN_ID = "demo_2026-03-08"
EXPECTED_PLOTS = ["demo_plot_01", "demo_plot_02", "demo_plot_03", "demo_plot_04"]
REQUIRED_ARTIFACTS = ["report.html", "report.json", "manifest.sha256"]
OPTIONAL_ARTIFACTS = ["report.pdf"]


def validate(site_root: Path) -> list[str]:
    errors: list[str] = []

    sample_reports_root = site_root / "sample_reports"
    runs_root = sample_reports_root / "runs" / SAMPLE_REPORTS_RUN_ID
    index_file = sample_reports_root / "index.html"

    if not index_file.is_file():
        errors.append(f"missing index: {index_file}")

    if not runs_root.is_dir():
        errors.append(f"missing sample reports run folder: {runs_root}")

    index_text = index_file.read_text(encoding="utf-8") if index_file.is_file() else ""

    for plot_id in EXPECTED_PLOTS:
        plot_dir = runs_root / plot_id
        if not plot_dir.is_dir():
            errors.append(f"missing plot folder: {plot_dir}")
            continue

        if index_text and plot_id not in index_text:
            errors.append(f"plot id not referenced in index.html: {plot_id}")

        for artifact in REQUIRED_ARTIFACTS:
            artifact_path = plot_dir / artifact
            if not artifact_path.is_file():
                errors.append(f"missing artifact: {artifact_path}")

        for artifact in OPTIONAL_ARTIFACTS:
            artifact_path = plot_dir / artifact
            if artifact_path.exists() and not artifact_path.is_file():
                errors.append(f"artifact is not a file: {artifact_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate sample reports index and run artifacts.")
    parser.add_argument(
        "--site-root",
        default=str(Path(__file__).resolve().parents[1] / "docs" / "site"),
        help="Path to docs/site root (default: repo/docs/site)",
    )
    args = parser.parse_args()

    errors = validate(Path(args.site_root))
    if errors:
        print("Sample reports validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Sample reports validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
