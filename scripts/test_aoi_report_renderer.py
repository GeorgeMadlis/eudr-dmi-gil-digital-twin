#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from aoi_report_renderer import load_report, render_aoi_run, update_evidence_hashes, write_report


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "docs/site/aoi_reports/runs/example"


def copy_fixture(tmp_dir: Path) -> Path:
    run_dir = tmp_dir / "example"
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE_DIR / "aoi_report.json", run_dir / "aoi_report.json")
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE_DIR / "inputs" / "aoi.geojson", inputs_dir / "aoi.geojson")
    return run_dir


def ensure_declared_artifacts_exist(run_dir: Path, report: dict) -> None:
    for entry in report.get("evidence_artifacts", []):
        relpath = entry.get("relpath")
        if not relpath:
            continue
        artifact_path = run_dir / relpath
        if artifact_path.is_file():
            continue
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        # Deterministic placeholder content for declared-but-not-generated artefacts.
        artifact_path.write_bytes(b"placeholder\n")


def render_once(tmp_dir: Path) -> dict[str, bytes]:
    run_dir = copy_fixture(tmp_dir)
    report = load_report(run_dir / "aoi_report.json")
    ensure_declared_artifacts_exist(run_dir, report)
    render_aoi_run(run_dir)
    updated = update_evidence_hashes(run_dir, report)
    write_report(run_dir / "aoi_report.json", updated)
    outputs = {}
    for relpath in [
        "reports/aoi_report_v1/estonia_testland1.html",
        "reports/aoi_report_v1/estonia_testland1.json",
        "reports/aoi_report_v1/estonia_testland1/metrics.csv",
    ]:
        outputs[relpath] = (run_dir / relpath).read_bytes()
    return outputs


def main() -> int:
    with tempfile.TemporaryDirectory() as dir_one, tempfile.TemporaryDirectory() as dir_two:
        out_one = render_once(Path(dir_one))
        out_two = render_once(Path(dir_two))

    if out_one != out_two:
        raise SystemExit("Deterministic render test failed: outputs differ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
