#!/usr/bin/env python3
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from aoi_report_renderer import (
    find_artifact_relpath,
    find_html_relpath,
    load_report,
    render_aoi_run,
    update_evidence_hashes,
    write_report,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "docs/site/bundles/runs/example"


def copy_fixture(tmp_dir: Path) -> Path:
    run_dir = tmp_dir / "example"
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE_DIR / "estonia_aoi_report.json", run_dir / "aoi_report.json")
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
    html_relpath = find_html_relpath(updated)
    json_relpath = find_artifact_relpath(updated, ".json")
    metrics_relpath = find_artifact_relpath(updated, "metrics.csv")
    outputs = {}
    for relpath in [
        "report.html",
        html_relpath,
        json_relpath,
        metrics_relpath,
    ]:
        outputs[relpath] = (run_dir / relpath).read_bytes()
    return outputs


def assert_post2020_evidence_section(outputs: dict[str, bytes]) -> None:
    html_text = outputs["reports/aoi_report_v2/estonia_testland1.html"].decode("utf-8")
    overview_text = outputs["report.html"].decode("utf-8")
    json_text = outputs["reports/aoi_report_v2/estonia_testland1.json"].decode("utf-8")

    required_html = [
        "Post-2020 deforestation evidence",
        "2021–2025",
        "Dataset temporal coverage",
        "Evidence gap",
        "Conflict register",
        "Agricultural conversion evidence missing",
        "does not assert EUDR compliance or non-compliance",
    ]
    for needle in required_html:
        if needle not in html_text:
            raise SystemExit(f"Missing post-2020 evidence HTML marker: {needle}")

    if "Post-2020 deforestation evidence" not in overview_text:
        raise SystemExit("Run overview is missing the post-2020 evidence card")

    if "post2020_deforestation_evidence" not in json_text:
        raise SystemExit("Rendered report JSON is missing post2020_deforestation_evidence")


def main() -> int:
    with tempfile.TemporaryDirectory() as dir_one, tempfile.TemporaryDirectory() as dir_two:
        out_one = render_once(Path(dir_one))
        out_two = render_once(Path(dir_two))

    if out_one != out_two:
        raise SystemExit("Deterministic render test failed: outputs differ")
    assert_post2020_evidence_section(out_one)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
