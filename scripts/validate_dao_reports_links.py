#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


EXPECTED_PLOTS = ["demo_plot_01", "demo_plot_02", "demo_plot_03"]
EXPECTED_ARTIFACTS = ["report.html", "report.pdf", "report.json"]


def validate(site_root: Path) -> list[str]:
    errors: list[str] = []

    dao_root = site_root / "dao_reports"
    runs_dir = dao_root / "runs"
    index_file = dao_root / "index.html"

    if not index_file.is_file():
        errors.append(f"missing index: {index_file}")

    if not runs_dir.is_dir():
        errors.append(f"missing runs dir: {runs_dir}")
        return errors

    run_dirs = sorted([p for p in runs_dir.iterdir() if p.is_dir()])
    if not run_dirs:
        errors.append(f"no run directories found in: {runs_dir}")
        return errors

    index_text = index_file.read_text(encoding="utf-8") if index_file.is_file() else ""

    for run_dir in run_dirs:
        run_id = run_dir.name
        if index_text and run_id not in index_text:
            errors.append(f"run id not referenced in index.html: {run_id}")

        for plot_id in EXPECTED_PLOTS:
            plot_dir = run_dir / plot_id
            if not plot_dir.is_dir():
                errors.append(f"missing plot folder: {plot_dir}")
                continue
            for artifact in EXPECTED_ARTIFACTS:
                artifact_path = plot_dir / artifact
                if not artifact_path.is_file():
                    errors.append(f"missing artifact: {artifact_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DAO reports index and run artifacts.")
    parser.add_argument(
        "--site-root",
        default=str(Path(__file__).resolve().parents[1] / "docs" / "site"),
        help="Path to docs/site root (default: repo/docs/site)",
    )
    args = parser.parse_args()

    errors = validate(Path(args.site_root))
    if errors:
        print("DAO reports validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("DAO reports validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
