#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import html
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass(frozen=True)
class RenderedArtifacts:
    html_relpath: str
    json_relpath: str
    metrics_relpath: str


@dataclass(frozen=True)
class StaticMapArtifacts:
    svg_relpath: str
    png_relpath: str
    satellite_png_relpath: str | None = None


DEFAULT_MAP_WIDTH_PX = 1100
DEFAULT_MAP_HEIGHT_PX = 760
DEFAULT_MAP_PADDING_PX = 40.0

MAP_LAYER_STYLES: dict[str, dict[str, Any]] = {
    "forest_2000": {
        "label": "Forest cover 2000",
        "stroke": "#2e7d32",
        "fill": "#2e7d32",
        "fill_opacity": 0.25,
        "stroke_width": 1.0,
    },
    "forest_end_year": {
        "label": "Forest cover {latest_year}",
        "stroke": "#1b5e20",
        "fill": "#1b5e20",
        "fill_opacity": 0.30,
        "stroke_width": 1.0,
    },
    "forest_loss_post_2020": {
        "label": "Forest loss since 2020",
        "stroke": "#c62828",
        "fill": "#c62828",
        "fill_opacity": 0.55,
        "stroke_width": 1.2,
    },
    "aoi_boundary": {
        "label": "AOI boundary",
        "stroke": "#00e5ff",
        "fill": "none",
        "fill_opacity": 0.0,
        "stroke_width": 2.4,
    },
    "parcels": {
        "label": "Maa-amet parcels",
        "stroke": "#6a1b9a",
        "fill": "#6a1b9a",
        "fill_opacity": 0.05,
        "stroke_width": 1.0,
    },
}

MAP_LAYER_FALLBACK_COLORS = [
    "#ef6c00",
    "#3949ab",
    "#00838f",
    "#ad1457",
    "#455a64",
]


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_artifact_relpath(report: dict[str, Any], suffix: str) -> str:
    for entry in report.get("evidence_artifacts", []):
        relpath = entry.get("relpath", "")
        if relpath.endswith(suffix):
            return relpath
    raise ValueError(f"No evidence_artifacts entry ends with {suffix}")


def find_html_relpath(report: dict[str, Any]) -> str:
    for entry in report.get("evidence_artifacts", []):
        relpath = entry.get("relpath", "")
        if relpath.endswith(".html"):
            return relpath
    raise ValueError("No HTML evidence_artifacts entry found")


def relpath_from_html(run_dir: Path, html_path: Path, target_relpath: str) -> str:
    target_path = run_dir / target_relpath
    rel = os.path.relpath(target_path, html_path.parent)
    return Path(rel).as_posix()


def render_metrics_rows(report: dict[str, Any]) -> list[dict[str, str]]:
    metrics = report.get("metrics", {})
    rows = []
    sources = {}
    for row in report.get("extensions", {}).get("metrics_rows_v1", []):
        variable = row.get("variable")
        if variable:
            sources[variable] = row.get("source", "")
    for key in sorted(metrics.keys()):
        entry = metrics.get(key, {})
        rows.append(
            {
                "variable": key,
                "value": str(entry.get("value", "")),
                "unit": str(entry.get("unit", "")),
                "notes": str(entry.get("notes", "")),
                "source": str(sources.get(key, "")),
            }
        )
    return rows


def render_metrics_csv(report: dict[str, Any]) -> str:
    rows = render_metrics_rows(report)
    output = []
    header = ["variable", "value", "unit", "notes", "source"]
    output.append(header)
    for row in rows:
        output.append([row[h] for h in header])
    with_rows = []
    for row in output:
        with_rows.append(row)
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(with_rows)
    return buffer.getvalue()


def render_report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _metric_value(report: dict[str, Any], key: str, default: Any = None) -> Any:
    entry = report.get("metrics", {}).get(key) if isinstance(report.get("metrics"), dict) else None
    if isinstance(entry, dict) and "value" in entry:
        return entry.get("value")
    return default


def _fmt_value(value: Any, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False) + suffix
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".") + suffix
    return str(value) + suffix


def _latest_hansen_dataset(report: dict[str, Any]) -> dict[str, Any]:
    for dataset in report.get("datasets", []) or []:
        if not isinstance(dataset, dict):
            continue
        dataset_id = str(dataset.get("dataset_id", ""))
        if dataset_id.startswith("hansen_gfc_"):
            return dataset
    return {}


def _legacy_post2020_evidence(report: dict[str, Any]) -> dict[str, Any]:
    forest_metrics = report.get("forest_metrics") if isinstance(report.get("forest_metrics"), dict) else {}
    computed = report.get("computed", {}) if isinstance(report.get("computed"), dict) else {}
    computed_loss = (
        computed.get("forest_loss_post_2020", {})
        if isinstance(computed.get("forest_loss_post_2020"), dict)
        else {}
    )
    map_assets = report.get("map_assets") if isinstance(report.get("map_assets"), dict) else {}
    end_year = forest_metrics.get("end_year") or _metric_value(report, "end_year") or map_assets.get("latest_year")
    try:
        resolved_end_year = int(end_year) if end_year is not None else 2025
    except (TypeError, ValueError):
        resolved_end_year = 2025
    start_year = 2021
    loss_key = f"loss_{start_year}_{resolved_end_year}_ha"
    hansen_dataset = _latest_hansen_dataset(report)
    hansen_version = str(hansen_dataset.get("version", f"{resolved_end_year}-v1.13"))
    hansen_asset = "UMD/hansen/global_forest_change_" + hansen_version.replace("-", "_").replace(".", "_")
    aoi_area = _metric_value(report, "aoi_area_ha")
    forest_area = (
        forest_metrics.get("rfm_area_ha")
        or computed_loss.get("pixel_initial_tree_cover_ha")
        or _metric_value(report, "rfm_area_ha")
        or _metric_value(report, "pixel_initial_tree_cover_ha")
    )
    forest_share = (float(forest_area) / float(aoi_area)) if forest_area and aoi_area else None
    disturbance_ha = (
        forest_metrics.get(loss_key)
        or computed_loss.get("pixel_forest_loss_post_2020_ha")
        or _metric_value(report, loss_key)
        or _metric_value(report, "pixel_forest_loss_post_2020_ha")
        or 0.0
    )
    human_review_required = bool(float(disturbance_ha or 0.0) > 0.0)
    state = (
        "post2020_disturbance_detected_agricultural_conversion_evidence_missing"
        if human_review_required
        else "insufficient_evidence"
    )

    return {
        "period": {
            "start_year": start_year,
            "requested_end_year": "auto",
            "resolved_end_year": resolved_end_year,
            "end_year_resolution_mode": "auto_latest_available_complete_evidence_year",
            "notice": (
                "The resolved end year reflects dataset availability, not necessarily "
                "the current calendar year."
            ),
        },
        "baseline": {
            "dataset": "JRC/GFC2020/V3",
            "role": "forest_baseline_2020",
            "baseline_year": 2020,
            "aoi_area_ha": aoi_area,
            "forest_area_ha": forest_area,
            "forest_share": forest_share,
            "display_name": "JRC GFC2020",
            "resolution": "30 m evidence grid / provider-native raster",
        },
        "dataset_versions": {
            "gfc2020": {
                "asset_id": "JRC/GFC2020/V3",
                "role": "forest_baseline_2020",
                "latest_available_year": 2020,
                "used_through_year": 2020,
            },
            "hansen_gfc": {
                "asset_id": hansen_asset,
                "latest_available_year": resolved_end_year,
                "used_through_year": resolved_end_year,
            },
            "jrc_tmf": {
                "asset_id": "projects/JRC/TMF/v1_2025",
                "latest_available_year": 2025,
                "used_through_year": None,
            },
            "radd": {
                "asset_id": "projects/radar-wur/raddalert/v1",
                "latest_available_year": None,
                "used_through_year": None,
            },
            "sentinel_confirmation": {
                "asset_id": "provider_configured_sentinel_confirmation",
                "latest_available_year": None,
                "used_through_year": None,
            },
        },
        "disturbance": {
            "hansen_loss_2021_resolved_end_year_ha": disturbance_ha,
            "tmf_deforestation_2021_resolved_end_year_ha": None,
            "tmf_degradation_2021_resolved_end_year_ha": None,
            "radd_confirmed_alert_2021_resolved_end_year_ha": None,
            "radd_low_confidence_alert_2021_resolved_end_year_ha": None,
            "sentinel_confirmation": {"dnbr": None, "dndvi": None, "dvh": None},
            "union_disturbance_candidate_ha": disturbance_ha,
        },
        "metrics_by_year": {"hansen_loss_inside_gfc2020_ha": {}},
        "conversion": {
            "agricultural_conversion_evidence": "missing",
            "commodity_layer": None,
            "land_use_layer": None,
        },
        "evidence_state": state,
        "human_review_required": human_review_required,
        "warnings": [
            {
                "code": "legacy_hansen_only_evidence",
                "message": (
                    "This public bundle predates full optional-layer computation; TMF, RADD, "
                    "Sentinel confirmation, and agricultural-conversion evidence are shown "
                    "as explicit evidence gaps."
                ),
            }
        ],
        "conflict_register": [],
        "non_decision_notice": (
            "This report provides evidence metrics only and does not assert EUDR "
            "compliance or non-compliance."
        ),
    }


def post2020_evidence(report: dict[str, Any]) -> dict[str, Any]:
    evidence = report.get("post2020_deforestation_evidence")
    if isinstance(evidence, dict):
        return evidence
    return _legacy_post2020_evidence(report)


def _period_label(period: dict[str, Any]) -> str:
    start = period.get("start_year", 2021)
    end = period.get("resolved_end_year", "unknown")
    return f"{start}–{end}"


def _layer_period(start_year: Any, used_through_year: Any) -> str:
    if used_through_year is None or used_through_year == "":
        return "not available"
    if used_through_year == 2020:
        return "2020"
    return f"{start_year}–{used_through_year}"


def render_post2020_evidence_section(report: dict[str, Any]) -> str:
    evidence = post2020_evidence(report)
    period = evidence.get("period", {}) if isinstance(evidence.get("period"), dict) else {}
    baseline = evidence.get("baseline", {}) if isinstance(evidence.get("baseline"), dict) else {}
    versions = evidence.get("dataset_versions", {}) if isinstance(evidence.get("dataset_versions"), dict) else {}
    disturbance = evidence.get("disturbance", {}) if isinstance(evidence.get("disturbance"), dict) else {}
    conversion = evidence.get("conversion", {}) if isinstance(evidence.get("conversion"), dict) else {}
    metrics_by_year = evidence.get("metrics_by_year", {}) if isinstance(evidence.get("metrics_by_year"), dict) else {}
    yearly_hansen = (
        metrics_by_year.get("hansen_loss_inside_gfc2020_ha", {})
        if isinstance(metrics_by_year.get("hansen_loss_inside_gfc2020_ha"), dict)
        else {}
    )
    start_year = period.get("start_year", 2021)
    resolved_end_year = period.get("resolved_end_year")
    warnings = [w for w in evidence.get("warnings", []) or [] if isinstance(w, dict)]
    conflicts = [c for c in evidence.get("conflict_register", []) or [] if isinstance(c, dict)]
    state = str(evidence.get("evidence_state", "insufficient_evidence"))
    human_review = bool(evidence.get("human_review_required", False))

    def version(dataset_id: str, key: str, default: Any = None) -> Any:
        entry = versions.get(dataset_id, {})
        return entry.get(key, default) if isinstance(entry, dict) else default

    layer_rows = [
        {
            "layer": "JRC GFC2020",
            "role": "2020 forest baseline",
            "period": "2020",
            "latest": version("gfc2020", "latest_available_year", 2020),
            "asset": baseline.get("dataset") or version("gfc2020", "asset_id", "JRC/GFC2020/V3"),
            "metric": "Forest area in AOI",
            "result": _fmt_value(baseline.get("forest_area_ha"), " ha"),
            "interpretation": "Baseline forest evidence",
        },
        {
            "layer": "Hansen GFC",
            "role": "Annual loss",
            "period": _layer_period(start_year, version("hansen_gfc", "used_through_year", resolved_end_year)),
            "latest": version("hansen_gfc", "latest_available_year"),
            "asset": version("hansen_gfc", "asset_id", "UMD/hansen/global_forest_change"),
            "metric": "Loss inside GFC2020 forest",
            "result": _fmt_value(disturbance.get("hansen_loss_2021_resolved_end_year_ha"), " ha"),
            "interpretation": "Post-2020 disturbance signal",
        },
        {
            "layer": "JRC TMF",
            "role": "Tropical forest dynamics",
            "period": _layer_period(start_year, version("jrc_tmf", "used_through_year")),
            "latest": version("jrc_tmf", "latest_available_year"),
            "asset": version("jrc_tmf", "asset_id", "projects/JRC/TMF/v1_2025"),
            "metric": "Deforestation/degradation",
            "result": (
                f"{_fmt_value(disturbance.get('tmf_deforestation_2021_resolved_end_year_ha'), ' ha')} / "
                f"{_fmt_value(disturbance.get('tmf_degradation_2021_resolved_end_year_ha'), ' ha')}"
            ),
            "interpretation": "Optional, geography-dependent evidence",
        },
        {
            "layer": "RADD",
            "role": "Near-real-time radar alerts",
            "period": _layer_period(start_year, version("radd", "used_through_year")),
            "latest": version("radd", "latest_available_year"),
            "asset": version("radd", "asset_id", "projects/radar-wur/raddalert/v1"),
            "metric": "Confirmed / low-confidence alerts",
            "result": (
                f"{_fmt_value(disturbance.get('radd_confirmed_alert_2021_resolved_end_year_ha'), ' ha')} / "
                f"{_fmt_value(disturbance.get('radd_low_confidence_alert_2021_resolved_end_year_ha'), ' ha')}"
            ),
            "interpretation": "Alert-based disturbance evidence",
        },
        {
            "layer": "Sentinel-1/2",
            "role": "Local confirmation",
            "period": _layer_period(start_year, version("sentinel_confirmation", "used_through_year")),
            "latest": version("sentinel_confirmation", "latest_available_year"),
            "asset": version("sentinel_confirmation", "asset_id", "provider_configured_sentinel_confirmation"),
            "metric": "dNBR / dNDVI / dVH",
            "result": _fmt_value(disturbance.get("sentinel_confirmation")),
            "interpretation": "Corroboration / challenge layer",
        },
        {
            "layer": "Commodity / land-use layer",
            "role": "Agricultural conversion",
            "period": "configured dates",
            "latest": "n/a",
            "asset": conversion.get("commodity_layer") or conversion.get("land_use_layer") or "not configured",
            "metric": "Conversion evidence",
            "result": conversion.get("agricultural_conversion_evidence", "missing"),
            "interpretation": "Needed for EUDR interpretation",
        },
    ]

    lines: list[str] = []
    lines.append("  <h2>Post-2020 deforestation evidence</h2>")
    lines.append(
        "  <p>JRC GFC2020 is used here as a 2020 forest-baseline layer. "
        "Post-2020 disturbance layers are intersected with the baseline forest mask "
        "to estimate whether forest disturbance occurred after the EUDR cut-off date. "
        "The reporting period is resolved from the latest available evidence datasets "
        "and may not equal the current calendar year. These metrics do not by themselves "
        "establish EUDR deforestation, because EUDR deforestation also requires conversion "
        "of forest to agricultural use. Agricultural or commodity-conversion evidence is "
        "therefore reported separately.</p>"
    )
    lines.append("  <table>")
    lines.append("    <tr><th>Field</th><th>Value</th></tr>")
    lines.append(f"    <tr><td>Evidence period</td><td>{html.escape(_period_label(period))}</td></tr>")
    lines.append(
        "    <tr><td>Requested end year</td>"
        f"<td><code>{html.escape(json.dumps(period.get('requested_end_year'), ensure_ascii=False))}</code></td></tr>"
    )
    lines.append(
        "    <tr><td>Resolution mode</td>"
        f"<td><code>{html.escape(str(period.get('end_year_resolution_mode', '')))}</code></td></tr>"
    )
    lines.append(
        "    <tr><td>Resolved end year notice</td>"
        f"<td>{html.escape(str(period.get('notice', 'The resolved end year reflects dataset availability, not necessarily the current calendar year.')))}</td></tr>"
    )
    lines.append(f"    <tr><td>AOI area</td><td>{html.escape(_fmt_value(baseline.get('aoi_area_ha'), ' ha'))}</td></tr>")
    lines.append(f"    <tr><td>GFC2020 forest share</td><td>{html.escape(_fmt_value(baseline.get('forest_share')))}</td></tr>")
    lines.append(
        "    <tr><td>Union disturbance candidate area</td>"
        f"<td>{html.escape(_fmt_value(disturbance.get('union_disturbance_candidate_ha'), ' ha'))}</td></tr>"
    )
    lines.append(f"    <tr><td>Evidence state</td><td><strong>{html.escape(state)}</strong></td></tr>")
    lines.append(f"    <tr><td>Human review required</td><td>{html.escape(str(human_review))}</td></tr>")
    lines.append(
        "    <tr><td>Non-decision notice</td>"
        f"<td>{html.escape(str(evidence.get('non_decision_notice', 'This report provides evidence metrics only and does not assert EUDR compliance or non-compliance.')))}</td></tr>"
    )
    lines.append("  </table>")

    lines.append("  <h3>Evidence layers</h3>")
    lines.append("  <table>")
    lines.append(
        "    <tr><th>Evidence layer</th><th>Role</th><th>Period used</th>"
        "<th>Latest available year</th><th>Asset/version</th><th>Metric</th>"
        "<th>Result</th><th>Interpretation</th></tr>"
    )
    for row in layer_rows:
        row_style = " style=\"background:#fff8e1; border-left:4px solid #b26a00;\"" if row["period"] == "not available" else ""
        lines.append(
            f"    <tr{row_style}>"
            f"<td>{html.escape(str(row['layer']))}</td>"
            f"<td>{html.escape(str(row['role']))}</td>"
            f"<td>{html.escape(str(row['period']))}</td>"
            f"<td>{html.escape(_fmt_value(row['latest']))}</td>"
            f"<td><code>{html.escape(str(row['asset']))}</code></td>"
            f"<td>{html.escape(str(row['metric']))}</td>"
            f"<td>{html.escape(str(row['result']))}</td>"
            f"<td>{html.escape(str(row['interpretation']))}</td>"
            "</tr>"
        )
    lines.append("  </table>")

    lines.append("  <h3>Dataset temporal coverage</h3>")
    lines.append("  <table>")
    lines.append("    <tr><th>Dataset</th><th>Latest available year</th><th>Used-through year</th><th>Coverage note</th></tr>")
    for dataset_id in sorted(versions):
        entry = versions.get(dataset_id, {})
        if not isinstance(entry, dict):
            continue
        latest = entry.get("latest_available_year")
        used = entry.get("used_through_year")
        note = ""
        if latest is None or used is None:
            note = "Evidence gap: temporal coverage is unavailable or provider/geography-dependent."
        elif resolved_end_year is not None and used < resolved_end_year and dataset_id != "gfc2020":
            note = "Evidence gap: layer coverage is lower than the resolved end year."
        lines.append(
            "    <tr>"
            f"<td><code>{html.escape(str(dataset_id))}</code></td>"
            f"<td>{html.escape(_fmt_value(latest))}</td>"
            f"<td>{html.escape(_fmt_value(used))}</td>"
            f"<td>{html.escape(note)}</td>"
            "</tr>"
        )
    lines.append("  </table>")

    if yearly_hansen:
        lines.append("  <h3>Hansen annual loss inside GFC2020 forest</h3>")
        lines.append("  <table>")
        lines.append("    <tr><th>Year</th><th>Area (ha)</th></tr>")
        for year in sorted(yearly_hansen, key=str):
            lines.append(
                "    <tr>"
                f"<td>{html.escape(str(year))}</td>"
                f"<td>{html.escape(_fmt_value(yearly_hansen.get(year)))}</td>"
                "</tr>"
            )
        lines.append("  </table>")

    lines.append("  <h3>Evidence gap</h3>")
    if conversion.get("agricultural_conversion_evidence") != "present":
        lines.append(
            "  <div style=\"background:#fff8e1; border-left:4px solid #b26a00; padding:10px;\">"
            "<strong>Agricultural conversion evidence missing.</strong> Disturbance evidence "
            "is not the same as agricultural conversion evidence.</div>"
        )
    else:
        lines.append("  <p>Agricultural conversion evidence is declared as present.</p>")

    lines.append("  <h3>Conflict register</h3>")
    if conflicts:
        lines.append("  <table>")
        lines.append("    <tr><th>Conflict</th><th>Details</th></tr>")
        for conflict in conflicts:
            label = conflict.get("code") or conflict.get("dataset_id") or "conflict"
            lines.append(
                "    <tr style=\"background:#fff5f5; border-left:4px solid #b00020;\">"
                f"<td>{html.escape(str(label))}</td>"
                f"<td><code>{html.escape(json.dumps(conflict, sort_keys=True, ensure_ascii=False))}</code></td>"
                "</tr>"
            )
        lines.append("  </table>")
    else:
        lines.append("  <p class=\"muted\">No dataset conflicts declared.</p>")

    if warnings:
        lines.append("  <h3>Warnings</h3>")
        lines.append("  <ul>")
        for warning in warnings:
            message = warning.get("message") or json.dumps(warning, sort_keys=True, ensure_ascii=False)
            lines.append(f"    <li>{html.escape(str(message))}</li>")
        lines.append("  </ul>")

    lines.append("  <h3>Limitations</h3>")
    limitations = evidence.get("limitations") or [
        "GFC2020 is not a legal determination.",
        "Tree-cover loss is not automatically EUDR deforestation.",
        "Conversion to agricultural use must be supported by additional evidence.",
        "Dataset conflicts must be exposed, not hidden.",
        "The report is an evidence report, not a compliance certificate.",
        "The evidence period depends on dataset availability and may lag the current calendar year.",
    ]
    lines.append("  <ul>")
    for limitation in limitations:
        lines.append(f"    <li>{html.escape(str(limitation))}</li>")
    lines.append("  </ul>")
    return "\n".join(lines)


def render_post2020_overview_card(report: dict[str, Any]) -> str:
    evidence = post2020_evidence(report)
    period = evidence.get("period", {}) if isinstance(evidence.get("period"), dict) else {}
    disturbance = evidence.get("disturbance", {}) if isinstance(evidence.get("disturbance"), dict) else {}
    conversion = evidence.get("conversion", {}) if isinstance(evidence.get("conversion"), dict) else {}
    versions = evidence.get("dataset_versions", {}) if isinstance(evidence.get("dataset_versions"), dict) else {}
    state = str(evidence.get("evidence_state", "insufficient_evidence"))
    human_review = bool(evidence.get("human_review_required", False))
    conversion_status = str(conversion.get("agricultural_conversion_evidence", "missing"))
    gap_count = 0
    for dataset_id, entry in versions.items():
        if not isinstance(entry, dict) or dataset_id == "gfc2020":
            continue
        if entry.get("latest_available_year") is None or entry.get("used_through_year") is None:
            gap_count += 1
    if conversion_status != "present":
        gap_count += 1

    lines = [
        "      <div class=\"card\">",
        "        <h2>Post-2020 deforestation evidence</h2>",
        "        <p>Evidence metrics only; this page does not assert EUDR compliance or non-compliance.</p>",
        "        <ul>",
        f"          <li>Evidence period: <code>{html.escape(_period_label(period))}</code> "
        f"({html.escape(str(period.get('end_year_resolution_mode', '')))}).</li>",
        "          <li>Union disturbance candidate area: <code>"
        + html.escape(_fmt_value(disturbance.get("union_disturbance_candidate_ha"), " ha"))
        + "</code>.</li>",
        f"          <li>Evidence state: <code>{html.escape(state)}</code>; human review required: <code>{html.escape(str(human_review))}</code>.</li>",
        f"          <li>Agricultural conversion evidence: <code>{html.escape(conversion_status)}</code>.</li>",
        f"          <li>Visible evidence gaps: <code>{gap_count}</code>.</li>",
        "        </ul>",
        "      </div>",
    ]
    return "\n".join(lines)


def _properties_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _iter_outer_rings(geometry: dict[str, Any]) -> list[list[list[float]]]:
    geo_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if geo_type == "Polygon":
        return [coords[0]] if coords else []
    if geo_type == "MultiPolygon":
        rings: list[list[list[float]]] = []
        for polygon in coords:
            if polygon:
                rings.append(polygon[0])
        return rings
    return []


def _iter_rings(payload: dict[str, Any]) -> list[list[list[float]]]:
    payload_type = payload.get("type")
    if payload_type == "FeatureCollection":
        out: list[list[list[float]]] = []
        for feature in payload.get("features") or []:
            geometry = _properties_dict((feature or {}).get("geometry"))
            out.extend(_iter_outer_rings(geometry))
        return out
    if payload_type == "Feature":
        return _iter_outer_rings(_properties_dict(payload.get("geometry")))
    return _iter_outer_rings(payload)


def _bbox_from_rings(rings: list[list[list[float]]]) -> tuple[float, float, float, float] | None:
    lon_values: list[float] = []
    lat_values: list[float] = []
    for ring in rings:
        for point in ring:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            lon_values.append(float(point[0]))
            lat_values.append(float(point[1]))
    if not lon_values or not lat_values:
        return None
    return min(lon_values), min(lat_values), max(lon_values), max(lat_values)


def _expand_bbox(
    bbox: tuple[float, float, float, float],
    *,
    fraction: float = 0.08,
) -> tuple[float, float, float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox
    lon_pad = max((max_lon - min_lon) * fraction, 1e-6)
    lat_pad = max((max_lat - min_lat) * fraction, 1e-6)
    return (
        min_lon - lon_pad,
        min_lat - lat_pad,
        max_lon + lon_pad,
        max_lat + lat_pad,
    )


def _resolve_map_config(run_dir: Path, map_assets: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    config_relpath = str(map_assets.get("config_relpath", "")).strip()
    if not config_relpath:
        raise ValueError("map_assets.config_relpath is required for static map rendering")
    config_path = run_dir / config_relpath
    if not config_path.is_file():
        raise FileNotFoundError(f"Map config not found: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return config, config_path


def _resolve_map_layer_paths(config: dict[str, Any], config_path: Path) -> dict[str, Path]:
    layers = _properties_dict(config.get("layers"))
    resolved: dict[str, Path] = {}
    for key, relpath in layers.items():
        if not isinstance(relpath, str) or not relpath.strip():
            continue
        layer_path = (config_path.parent / relpath).resolve()
        if layer_path.is_file():
            resolved[key] = layer_path
    return resolved


def _layer_style(key: str, *, latest_year: int, index: int) -> dict[str, Any]:
    style = dict(MAP_LAYER_STYLES.get(key, {}))
    if not style:
        color = MAP_LAYER_FALLBACK_COLORS[index % len(MAP_LAYER_FALLBACK_COLORS)]
        style = {
            "label": key.replace("_", " ").title(),
            "stroke": color,
            "fill": color,
            "fill_opacity": 0.20,
            "stroke_width": 1.0,
        }
    label = str(style.get("label", key)).format(latest_year=latest_year)
    style["label"] = label
    return style


def _download_esri_satellite_png(
    *,
    bbox: tuple[float, float, float, float],
    width_px: int,
    height_px: int,
    output_path: Path,
) -> bytes | None:
    min_lon, min_lat, max_lon, max_lat = bbox
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width_px},{height_px}",
        "format": "png32",
        "f": "image",
    }
    url = (
        "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?"
        + urlencode(params)
    )
    try:
        with urlopen(url, timeout=20) as response:
            image_bytes = response.read()
        if not image_bytes:
            return None
        output_path.write_bytes(image_bytes)
        return image_bytes
    except Exception:
        if output_path.is_file():
            return output_path.read_bytes()
        return None


def _rings_to_svg_path(
    rings: list[list[list[float]]],
    *,
    project: Any,
) -> str:
    segments: list[str] = []
    for ring in rings:
        points: list[tuple[float, float]] = []
        for point in ring:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            points.append(project(float(point[0]), float(point[1])))
        if len(points) < 3:
            continue
        path_parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
        for x, y in points[1:]:
            path_parts.append(f"L {x:.2f} {y:.2f}")
        path_parts.append("Z")
        segments.append(" ".join(path_parts))
    return " ".join(segments)


def _rasterize_svg_to_png(svg_path: Path, png_path: Path) -> None:
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
        return
    except Exception:
        pass

    sips_path = shutil.which("sips")
    if sips_path:
        try:
            subprocess.run(
                [sips_path, "-s", "format", "png", str(svg_path), "--out", str(png_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if png_path.is_file():
                return
        except subprocess.CalledProcessError:
            pass

    qlmanage_path = shutil.which("qlmanage")
    if qlmanage_path:
        preview_dir = png_path.parent
        preview_name = f"{svg_path.name}.png"
        preview_path = preview_dir / preview_name
        try:
            if preview_path.is_file():
                preview_path.unlink()
            subprocess.run(
                [qlmanage_path, "-t", "-s", str(DEFAULT_MAP_WIDTH_PX), "-o", str(preview_dir), str(svg_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if preview_path.is_file():
                preview_path.replace(png_path)
                return
        except Exception:
            pass

    raise RuntimeError(
        "Unable to rasterize SVG to PNG; install cairosvg or ensure 'sips'/'qlmanage' are available"
    )


def render_static_map_image(
    *,
    run_dir: Path,
    map_assets: dict[str, Any],
    output_dir: Path,
    output_basename: str = "deforestation_map",
) -> StaticMapArtifacts:
    config, config_path = _resolve_map_config(run_dir, map_assets)
    layer_paths = _resolve_map_layer_paths(config, config_path)
    if "aoi_boundary" not in layer_paths:
        raise ValueError("Static map rendering requires an aoi_boundary layer")

    layers_in_order = list(_properties_dict(config.get("layers")).keys())
    resolved_layers = {
        key: _iter_rings(json.loads(path.read_text(encoding="utf-8")))
        for key, path in layer_paths.items()
    }
    all_rings: list[list[list[float]]] = []
    for rings in resolved_layers.values():
        all_rings.extend(rings)
    if not all_rings:
        raise ValueError(f"No polygon rings found in map layers for {config_path}")

    cfg_bbox = _properties_dict(config.get("aoi_bbox"))
    bbox: tuple[float, float, float, float] | None = None
    if cfg_bbox:
        try:
            bbox = (
                float(cfg_bbox["min_lon"]),
                float(cfg_bbox["min_lat"]),
                float(cfg_bbox["max_lon"]),
                float(cfg_bbox["max_lat"]),
            )
        except Exception:
            bbox = None
    if bbox is None:
        bbox = _bbox_from_rings(all_rings)
    if bbox is None:
        raise ValueError(f"Unable to determine bbox for static map from {config_path}")

    padded_bbox = _expand_bbox(bbox)
    min_lon, min_lat, max_lon, max_lat = padded_bbox
    span_lon = max(1e-12, max_lon - min_lon)
    span_lat = max(1e-12, max_lat - min_lat)
    latest_year = int(config.get("latest_year") or map_assets.get("latest_year") or 2024)

    width = float(DEFAULT_MAP_WIDTH_PX)
    height = float(DEFAULT_MAP_HEIGHT_PX)
    pad = DEFAULT_MAP_PADDING_PX
    plot_w = width - (2 * pad)
    plot_h = height - (2 * pad)

    output_dir.mkdir(parents=True, exist_ok=True)
    satellite_name = f"{output_basename}_satellite.png"
    satellite_path = output_dir / satellite_name
    satellite_bytes = _download_esri_satellite_png(
        bbox=padded_bbox,
        width_px=int(plot_w),
        height_px=int(plot_h),
        output_path=satellite_path,
    )
    satellite_data_uri = None
    if satellite_bytes is not None:
        encoded = base64.b64encode(satellite_bytes).decode("ascii")
        satellite_data_uri = f"data:image/png;base64,{encoded}"

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = pad + ((lon - min_lon) / span_lon) * plot_w
        y = pad + ((max_lat - lat) / span_lat) * plot_h
        return x, y

    svg_name = f"{output_basename}.svg"
    png_name = f"{output_basename}.png"
    svg_path = output_dir / svg_name
    png_path = output_dir / png_name

    svg_lines = [
        "<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" "
        f"width=\"{DEFAULT_MAP_WIDTH_PX}\" height=\"{DEFAULT_MAP_HEIGHT_PX}\" "
        f"viewBox=\"0 0 {DEFAULT_MAP_WIDTH_PX} {DEFAULT_MAP_HEIGHT_PX}\" role=\"img\" "
        "aria-label=\"Static AOI evidence map\">",
        "  <rect x=\"0\" y=\"0\" width=\"1100\" height=\"760\" fill=\"#ffffff\" />",
        "  <defs>",
        "    <clipPath id=\"map-clip\">",
        f"      <rect x=\"{pad:.2f}\" y=\"{pad:.2f}\" width=\"{plot_w:.2f}\" height=\"{plot_h:.2f}\" />",
        "    </clipPath>",
        "  </defs>",
        f"  <rect x=\"{pad:.2f}\" y=\"{pad:.2f}\" width=\"{plot_w:.2f}\" height=\"{plot_h:.2f}\" fill=\"#f4f4f4\" stroke=\"#d0d7de\" stroke-width=\"1\" />",
    ]
    if satellite_data_uri is not None:
        svg_lines.append(
            f"  <image href=\"{satellite_data_uri}\" xlink:href=\"{satellite_data_uri}\" "
            f"x=\"{pad:.2f}\" y=\"{pad:.2f}\" width=\"{plot_w:.2f}\" height=\"{plot_h:.2f}\" "
            "preserveAspectRatio=\"none\" clip-path=\"url(#map-clip)\" />"
        )

    legend_rows: list[tuple[str, str]] = []
    rendered_layer_count = 0
    for index, key in enumerate(layers_in_order):
        rings = resolved_layers.get(key)
        if not rings:
            continue
        style = _layer_style(key, latest_year=latest_year, index=index)
        path_data = _rings_to_svg_path(rings, project=project)
        if not path_data:
            continue
        fill = str(style.get("fill", "none"))
        fill_opacity = float(style.get("fill_opacity", 0.0))
        stroke = str(style.get("stroke", "#111111"))
        stroke_width = float(style.get("stroke_width", 1.0))
        svg_lines.append(
            f"  <path d=\"{path_data}\" fill=\"{fill}\" fill-opacity=\"{fill_opacity:.2f}\" "
            f"stroke=\"{stroke}\" stroke-width=\"{stroke_width:.2f}\" clip-path=\"url(#map-clip)\" />"
        )
        legend_rows.append((str(style.get("label", key)), stroke))
        rendered_layer_count += 1

    legend_height = max(88, 34 + (rendered_layer_count * 22))
    svg_lines.extend(
        [
            f"  <rect x=\"28\" y=\"28\" width=\"320\" height=\"{legend_height}\" fill=\"#ffffff\" fill-opacity=\"0.92\" stroke=\"#d0d7de\" />",
            "  <text x=\"42\" y=\"52\" font-size=\"18\" font-family=\"Arial, sans-serif\" fill=\"#111\">Static evidence map</text>",
        ]
    )
    for row_index, (label, color) in enumerate(legend_rows):
        y = 76 + (row_index * 22)
        svg_lines.append(
            f"  <text x=\"42\" y=\"{y}\" font-size=\"14\" font-family=\"Arial, sans-serif\" fill=\"{color}\">■ {html.escape(label)}</text>"
        )
    basemap_note_y = 76 + (len(legend_rows) * 22)
    basemap_note = "Basemap: Esri World Imagery" if satellite_data_uri is not None else "Basemap unavailable; overlays only"
    svg_lines.extend(
        [
            f"  <text x=\"42\" y=\"{basemap_note_y}\" font-size=\"11\" font-family=\"Arial, sans-serif\" fill=\"#666\">{html.escape(basemap_note)}</text>",
            "</svg>",
            "",
        ]
    )

    svg_path.write_text("\n".join(svg_lines), encoding="utf-8")
    _rasterize_svg_to_png(svg_path, png_path)

    return StaticMapArtifacts(
        svg_relpath=svg_name,
        png_relpath=png_name,
        satellite_png_relpath=satellite_name if satellite_bytes is not None else None,
    )


def render_report_html_static(
    report: dict[str, Any],
    run_dir: Path,
    html_relpath: str,
    *,
    static_map_png_relpath: str,
    static_map_svg_relpath: str | None = None,
) -> str:
    html_content = render_report_html(report, run_dir, html_relpath)
    map_assets = report.get("map_assets") if isinstance(report.get("map_assets"), dict) else None
    if not map_assets or not map_assets.get("config_relpath"):
        return html_content

    html_path = run_dir / html_relpath
    map_config_href = html.escape(relpath_from_html(run_dir, html_path, str(map_assets.get("config_relpath"))))
    static_png_href = html.escape(static_map_png_relpath)
    static_svg_link = ""
    if static_map_svg_relpath:
        static_svg_href = html.escape(static_map_svg_relpath)
        static_svg_link = f" · <a href=\"{static_svg_href}\">static SVG</a>"

    replacement = "\n".join(
        [
            "  <h2>Map (static)</h2>",
            f"  <p><a href=\"{map_config_href}\">map_config.json</a> · <a href=\"{static_png_href}\">static map PNG</a>{static_svg_link}</p>",
            "  <figure style=\"margin: 12px 0 16px;\">",
            f"    <img src=\"{static_png_href}\" alt=\"Static AOI evidence map\" style=\"max-width:100%; height:auto; border:1px solid #ddd; border-radius:8px; background:#fafafa;\" />",
            "  </figure>",
            "",
        ]
    )

    html_content = re.sub(
        r"\n  <link rel=\"stylesheet\" href=\"https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.css\" .*? />",
        "",
        html_content,
        count=1,
    )
    html_content = re.sub(
        r"\n  <script src=\"https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js\" .*?</script>",
        "",
        html_content,
        count=1,
    )
    html_content = re.sub(
        r"  <h2>Map \(interactive\)</h2>\n.*?(?=  <h2>Assumptions & Limitations</h2>)",
        replacement,
        html_content,
        count=1,
        flags=re.S,
    )
    return html_content


def render_report_html(report: dict[str, Any], run_dir: Path, html_relpath: str) -> str:
    html_path = run_dir / html_relpath
    aoi_id = str(report.get("aoi_id", ""))
    bundle_id = str(report.get("bundle_id", ""))
    report_version = str(report.get("report_version", ""))
    geometry_ref = report.get("aoi_geometry_ref", {})
    report_metadata = report.get("report_metadata")
    evidence_registry = report.get("evidence_registry")
    if evidence_registry is None and isinstance(report_metadata, dict):
        evidence_registry = report_metadata.get("evidence_registry")
    evidence_classes_list: list[dict[str, Any]] = []
    if isinstance(evidence_registry, dict):
        evidence_classes_list = [
            entry for entry in evidence_registry.get("evidence_classes", []) if isinstance(entry, dict)
        ]
    elif isinstance(evidence_registry, list):
        evidence_classes_list = [entry for entry in evidence_registry if isinstance(entry, dict)]
    acceptance_criteria = report.get("acceptance_criteria")
    if acceptance_criteria is None and isinstance(report_metadata, dict):
        acceptance_criteria = report_metadata.get("acceptance_criteria")
    results = report.get("results")
    regulatory_traceability = report.get("regulatory_traceability")
    assumptions = report.get("assumptions")
    if assumptions is None and isinstance(report_metadata, dict):
        assumptions = report_metadata.get("assumptions")
    map_assets = report.get("map_assets") if isinstance(report.get("map_assets"), dict) else None

    inputs = report.get("inputs", {}).get("sources", [])
    inputs_sorted = sorted(inputs, key=lambda item: str(item.get("source_id", "")))

    evidence = report.get("evidence_artifacts", [])
    evidence_sorted = sorted(evidence, key=lambda item: str(item.get("relpath", "")))

    criteria_alert_statuses = {"unmet", "unevaluable", "not_evaluable", "missing", "unknown", "not_evaluated"}

    def anchor_id(prefix: str, value: Any) -> str:
        safe = str(value).strip().replace(" ", "-")
        return f"{prefix}-{safe}"

    def format_criteria_refs(value: Any) -> str:
        if value is None:
            return "Not declared"
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else "Not declared"
        return str(value)

    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append('<html lang="en">')
    lines.append("<head>")
    lines.append("  <meta charset=\"utf-8\" />")
    lines.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />")
    lines.append(f"  <title>AOI Report Summary — {html.escape(aoi_id)}</title>")
    lines.append("  <style>")
    lines.append("    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }")
    lines.append("    table { border-collapse: collapse; width: 100%; }")
    lines.append("    th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; }")
    lines.append("    th { background: #f6f6f6; text-align: left; width: 240px; }")
    lines.append("    h2 { margin-top: 28px; }")
    lines.append("    .muted { color: #666; }")
    lines.append("    code { background: #f6f6f6; padding: 1px 4px; border-radius: 4px; }")
    lines.append("    #map { height: 420px; border: 1px solid #ddd; border-radius: 8px; margin: 12px 0 16px; background: #fafafa; }")
    lines.append("  </style>")
    if map_assets and map_assets.get("config_relpath"):
        lines.append(
            "  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" "
            "integrity=\"sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=\" crossorigin=\"\" />"
        )
        lines.append(
            "  <script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\" "
            "integrity=\"sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=\" crossorigin=\"\"></script>"
        )
    lines.append("</head>")
    lines.append("<body>")
    if not report_metadata:
        lines.append(
            "  <div style=\"border:2px solid #b00020; background:#fff5f5; padding:12px; margin-bottom:16px;\">"
            "<strong>INVALID FOR INSPECTION:</strong> report_metadata is missing."
            "</div>"
        )
    else:
        lines.append("  <h2>Report Intent & Scope</h2>")
        lines.append("  <table>")
        lines.append("    <tr><th>Field</th><th>Value</th></tr>")
        if isinstance(report_metadata, dict):
            for key in sorted(report_metadata.keys()):
                value = json.dumps(report_metadata[key], sort_keys=True, ensure_ascii=False)
                lines.append(
                    "    <tr>"
                    f"<td>{html.escape(str(key))}</td>"
                    f"<td><code>{html.escape(value)}</code></td>"
                    "</tr>"
                )
        else:
            value = json.dumps(report_metadata, sort_keys=True, ensure_ascii=False)
            lines.append(
                "    <tr>"
                "<td>value</td>"
                f"<td><code>{html.escape(value)}</code></td>"
                "</tr>"
            )
        lines.append("  </table>")
        lines.append("  <div style=\"height:12px;\"></div>")
        lines.append("  <h2>Regulatory traceability</h2>")
        if not regulatory_traceability:
            lines.append(
                "  <div style=\"border:2px solid #b00020; background:#fff5f5; padding:12px; margin-bottom:16px;\">"
                "<strong>Traceability not declared in report JSON</strong>"
                "</div>"
            )
        else:
            lines.append("  <table>")
            lines.append("    <tr><th>Regulation</th><th>Article</th><th>Evidence class</th><th>Acceptance criteria</th><th>Result ref</th></tr>")
            evidence_ids = {
                anchor_id("evidence", e.get("class_id") or e.get("class") or e.get("evidence_class") or e.get("id"))
                for e in evidence_classes_list
            }
            criteria_ids = {
                anchor_id(
                    "criteria",
                    c.get("criteria_id") or c.get("id") or c.get("name") or c.get("criteria"),
                )
                for c in acceptance_criteria or []
                if isinstance(c, dict)
            }
            result_ids = {anchor_id("result", r.get("result_id")) for r in results or [] if isinstance(r, dict) and r.get("result_id") is not None}

            def link_or_error(prefix: str, value: Any, declared_ids: set[str]) -> str:
                if value is None:
                    return "<strong>missing</strong>"
                anchor = anchor_id(prefix, value)
                if anchor in declared_ids:
                    return f"<a href=\"#{html.escape(anchor)}\">{html.escape(str(value))}</a>"
                return f"<strong>missing-link</strong> {html.escape(str(value))}"

            if isinstance(regulatory_traceability, list):
                for entry in regulatory_traceability:
                    if not isinstance(entry, dict):
                        value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                        lines.append(
                            "    <tr>"
                            f"<td colspan=\"5\"><code>{html.escape(value)}</code></td>"
                            "</tr>"
                        )
                        continue
                    regulation = entry.get("regulation")
                    article = entry.get("article_ref")
                    evidence_class = entry.get("evidence_class")
                    criteria = entry.get("acceptance_criteria")
                    result_ref = entry.get("result_ref")
                    lines.append(
                        "    <tr>"
                        f"<td>{html.escape(str(regulation)) if regulation is not None else '<strong>missing</strong>'}</td>"
                        f"<td>{html.escape(str(article)) if article is not None else '<strong>missing</strong>'}</td>"
                        f"<td>{link_or_error('evidence', evidence_class, evidence_ids)}</td>"
                        f"<td>{link_or_error('criteria', criteria, criteria_ids)}</td>"
                        f"<td>{link_or_error('result', result_ref, result_ids)}</td>"
                        "</tr>"
                    )
            else:
                value = json.dumps(regulatory_traceability, sort_keys=True, ensure_ascii=False)
                lines.append(
                    "    <tr>"
                    f"<td colspan=\"5\"><code>{html.escape(value)}</code></td>"
                    "</tr>"
                )
            lines.append("  </table>")
        lines.append("  <div style=\"height:12px;\"></div>")

    lines.append("  <h2>Evidence Registry</h2>")
    if not evidence_registry:
        lines.append(
            "  <div style=\"border:2px solid #b00020; background:#fff5f5; padding:12px; margin-bottom:16px;\">"
            "<strong>INVALID FOR INSPECTION:</strong> evidence_registry is missing."
            "</div>"
        )
    else:
        lines.append("  <table>")
        lines.append("    <tr><th>Evidence Class</th><th>Mandatory</th><th>Status</th></tr>")
        if evidence_classes_list:
            for entry in evidence_classes_list:
                if not isinstance(entry, dict):
                    value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                    lines.append(
                        "    <tr>"
                        "<td><code>value</code></td>"
                        "<td></td>"
                        f"<td><code>{html.escape(value)}</code></td>"
                        "</tr>"
                    )
                    continue
                evidence_class = entry.get("class_id") or entry.get("class") or entry.get("evidence_class") or entry.get("id")
                mandatory = entry.get("mandatory")
                status = entry.get("status")
                status_text = "" if status is None else str(status)
                mandatory_text = "" if mandatory is None else str(mandatory)
                is_missing = bool(mandatory is True and status_text.lower() in {"missing", "absent", "unavailable", "not_found"})
                row_style = " style=\"background:#fff5f5; border-left:4px solid #b00020;\"" if is_missing else ""
                evidence_id = anchor_id("evidence", evidence_class)
                lines.append(
                    f"    <tr{row_style}>"
                    f"<td id=\"{html.escape(evidence_id)}\">{html.escape(str(evidence_class))}</td>"
                    f"<td>{html.escape(mandatory_text)}</td>"
                    f"<td>{html.escape(status_text)}</td>"
                    "</tr>"
                )
        else:
            value = json.dumps(evidence_registry, sort_keys=True, ensure_ascii=False)
            lines.append(
                "    <tr>"
                "<td><code>value</code></td>"
                "<td></td>"
                f"<td><code>{html.escape(value)}</code></td>"
                "</tr>"
            )
        lines.append("  </table>")
        lines.append("  <div style=\"height:12px;\"></div>")

    lines.append("  <h2>Acceptance Criteria</h2>")
    if not acceptance_criteria:
        lines.append("  <p><em>No acceptance criteria declared.</em></p>")
    else:
        lines.append("  <table>")
        lines.append("    <tr><th>Criteria</th><th>Status</th><th>Details</th></tr>")
        if isinstance(acceptance_criteria, list):
            for entry in acceptance_criteria:
                if not isinstance(entry, dict):
                    value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                    lines.append(
                        "    <tr>"
                        f"<td><code>{html.escape(value)}</code></td>"
                        "<td></td>"
                        "<td></td>"
                        "</tr>"
                    )
                    continue
                criteria_id = entry.get("criteria_id") or entry.get("id") or entry.get("name") or entry.get("criteria")
                status = entry.get("status")
                status_text = "" if status is None else str(status)
                details_value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                is_alert = status_text.lower() in criteria_alert_statuses
                row_style = " style=\"background:#fff5f5; border-left:4px solid #b00020;\"" if is_alert else ""
                criteria_anchor = anchor_id("criteria", criteria_id)
                lines.append(
                    f"    <tr{row_style}>"
                    f"<td id=\"{html.escape(criteria_anchor)}\">{html.escape(str(criteria_id))}</td>"
                    f"<td>{html.escape(status_text)}</td>"
                    f"<td><code>{html.escape(details_value)}</code></td>"
                    "</tr>"
                )
        else:
            value = json.dumps(acceptance_criteria, sort_keys=True, ensure_ascii=False)
            lines.append(
                "    <tr>"
                f"<td><code>{html.escape(value)}</code></td>"
                "<td></td>"
                "<td></td>"
                "</tr>"
            )
        lines.append("  </table>")
    lines.append("  <div style=\"height:12px;\"></div>")
    lines.append("  <h1>AOI Report Summary</h1>")
    lines.append("  <table>")
    lines.append(f"    <tr><th>AOI</th><td>{html.escape(aoi_id)}</td></tr>")
    lines.append(f"    <tr><th>Bundle</th><td>{html.escape(bundle_id)}</td></tr>")
    lines.append(f"    <tr><th>Report Version</th><td>{html.escape(report_version)}</td></tr>")
    if geometry_ref:
        geometry_kind = html.escape(str(geometry_ref.get("kind", "")))
        geometry_value = html.escape(str(geometry_ref.get("value", "")))
        lines.append(f"    <tr><th>Geometry Ref</th><td>{geometry_kind}: {geometry_value}</td></tr>")
    lines.append("  </table>")

    lines.append("  <h2>Inputs</h2>")
    lines.append("  <table>")
    lines.append("    <tr><th>Source</th><th>URI</th><th>SHA256</th><th>Content Type</th></tr>")
    for source in inputs_sorted:
        lines.append(
            "    <tr>"
            f"<td>{html.escape(str(source.get('source_id', '')))}</td>"
            f"<td>{html.escape(str(source.get('uri', '')))}</td>"
            f"<td><code>{html.escape(str(source.get('sha256', '')))}</code></td>"
            f"<td>{html.escape(str(source.get('content_type', '')))}</td>"
            "</tr>"
        )
    lines.append("  </table>")

    lines.append(render_post2020_evidence_section(report))

    lines.append("  <h2>Metrics</h2>")
    lines.append("  <table>")
    lines.append("    <tr><th>Metric</th><th>Value</th><th>Unit</th><th>Notes</th><th>Source</th><th>Criteria</th></tr>")
    for row in render_metrics_rows(report):
        metric_entry = report.get("metrics", {}).get(row["variable"], {})
        criteria_refs = format_criteria_refs(metric_entry.get("criteria_refs") or metric_entry.get("acceptance_criteria"))
        lines.append(
            "    <tr>"
            f"<td>{html.escape(row['variable'])}</td>"
            f"<td>{html.escape(row['value'])}</td>"
            f"<td>{html.escape(row['unit'])}</td>"
            f"<td>{html.escape(row['notes'])}</td>"
            f"<td>{html.escape(row['source'])}</td>"
            f"<td>{html.escape(criteria_refs)}</td>"
            "</tr>"
        )
    lines.append("  </table>")

    validation = report.get("validation", {}) if isinstance(report.get("validation"), dict) else {}
    maaamet_validation = validation.get("maaamet", {}) if isinstance(validation.get("maaamet"), dict) else {}
    if maaamet_validation:
        lines.append("  <h2>Maa-amet parcels</h2>")
        lines.append("  <table>")
        lines.append("    <tr><th>Field</th><th>Value</th></tr>")
        for key in ["enabled", "parcel_layer", "parcel_count", "notes"]:
            if key in maaamet_validation:
                value = maaamet_validation.get(key)
                lines.append(
                    "    <tr>"
                    f"<td>{html.escape(key)}</td>"
                    f"<td><code>{html.escape(json.dumps(value, ensure_ascii=False))}</code></td>"
                    "</tr>"
                )
        for key in [
            "maaamet_land_area_ha_sum",
            "hansen_land_area_ha_sum",
            "land_area_diff_ha",
            "land_area_diff_pct",
        ]:
            if key in maaamet_validation:
                value = maaamet_validation.get(key)
                lines.append(
                    "    <tr>"
                    f"<td>{html.escape(key)}</td>"
                    f"<td><code>{html.escape(json.dumps(value, ensure_ascii=False))}</code></td>"
                    "</tr>"
                )
        lines.append("  </table>")

        parcels = maaamet_validation.get("parcels")
        if isinstance(parcels, list):
            lines.append("  <h3>Top 10 parcels (by forest area)</h3>")
            lines.append("  <table>")
            lines.append("    <tr><th>Parcel ID</th><th>Hansen land (ha)</th><th>Maa-amet land (ha)</th><th>Hansen forest (ha)</th><th>Maa-amet forest (ha)</th><th>Forest loss (ha)</th></tr>")
            if parcels:
                for row in parcels:
                    if not isinstance(row, dict):
                        continue
                    lines.append(
                        "    <tr>"
                        f"<td>{html.escape(str(row.get('parcel_id','')))}</td>"
                        f"<td>{html.escape(str(row.get('hansen_land_area_ha','')))}</td>"
                        f"<td>{html.escape(str(row.get('maaamet_land_area_ha','')))}</td>"
                        f"<td>{html.escape(str(row.get('hansen_forest_area_ha','')))}</td>"
                        f"<td>{html.escape(str(row.get('maaamet_forest_area_ha','')))}</td>"
                        f"<td>{html.escape(str(row.get('hansen_forest_loss_ha','')))}</td>"
                        "</tr>"
                    )
            else:
                lines.append("    <tr><td colspan=\"6\"><em>No Maa-amet parcels available.</em></td></tr>")
            lines.append("  </table>")

    forest_crosscheck = validation.get("forest_area_crosscheck", {}) if isinstance(validation.get("forest_area_crosscheck"), dict) else {}
    if forest_crosscheck:
        lines.append("  <h2>Hansen vs Maa-amet forest area crosscheck</h2>")
        lines.append("  <table>")
        lines.append("    <tr><th>Field</th><th>Value</th></tr>")
        for key in ["source", "outcome", "reason"]:
            if key in forest_crosscheck:
                lines.append(
                    "    <tr>"
                    f"<td>{html.escape(key)}</td>"
                    f"<td><code>{html.escape(json.dumps(forest_crosscheck.get(key), ensure_ascii=False))}</code></td>"
                    "</tr>"
                )
        for key in ["reference", "computed", "comparison"]:
            if key in forest_crosscheck:
                lines.append(
                    "    <tr>"
                    f"<td>{html.escape(key)}</td>"
                    f"<td><code>{html.escape(json.dumps(forest_crosscheck.get(key), ensure_ascii=False))}</code></td>"
                    "</tr>"
                )
        for ref_key in ["csv_ref", "summary_ref"]:
            ref = forest_crosscheck.get(ref_key)
            if isinstance(ref, dict):
                relpath = ref.get("relpath")
                if relpath:
                    href = html.escape(relpath_from_html(run_dir, html_path, str(relpath)))
                    lines.append(
                        "    <tr>"
                        f"<td>{html.escape(ref_key)}</td>"
                        f"<td><a href=\"{href}\">{html.escape(str(relpath))}</a></td>"
                        "</tr>"
                    )
        lines.append("  </table>")

    if map_assets and map_assets.get("config_relpath"):
        map_config_relpath = str(map_assets.get("config_relpath"))
        map_href = html.escape(relpath_from_html(run_dir, html_path, map_config_relpath))
        lines.append("  <h2>Map (interactive)</h2>")
        lines.append(f"  <p><a href=\"{map_href}\">map_config.json</a></p>")
        lines.append("  <div id=\"map\"></div>")
        lines.append("  <script>")
        lines.append("    (function () {")
        lines.append("      const map = L.map('map', { zoomControl: true });")
        lines.append("      const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {")
        lines.append("        attribution: 'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',")
        lines.append("      }).addTo(map);")
        lines.append(f"      const configUrl = '{map_href}';")
        lines.append("      fetch(configUrl)")
        lines.append("        .then((resp) => resp.json())")
        lines.append("        .then((config) => {")
        lines.append("          const bbox = config.aoi_bbox;")
        lines.append("          const bounds = L.latLngBounds([")
        lines.append("            [bbox.min_lat, bbox.min_lon],")
        lines.append("            [bbox.max_lat, bbox.max_lon],")
        lines.append("          ]);")
        lines.append("          map.fitBounds(bounds);")
        lines.append("          const overlays = {};")
        lines.append("          const baseLayers = { Satellite: satellite };")
        lines.append("          const addGeoJson = (label, url, options) => {")
        lines.append("            if (!url) return;")
        lines.append("            fetch(url)")
        lines.append("              .then((r) => r.json())")
        lines.append("              .then((data) => {")
        lines.append("                const layer = L.geoJSON(data, options).addTo(map);")
        lines.append("                overlays[label] = layer;")
        lines.append("              });")
        lines.append("          };")
        lines.append("          addGeoJson('Forest cover 2000', config.layers.forest_2000, { style: { color: '#2e7d32', weight: 1, fillOpacity: 0.3 } });")
        lines.append("          addGeoJson(`Forest cover ${config.latest_year}`, config.layers.forest_end_year, { style: { color: '#1b5e20', weight: 1, fillOpacity: 0.3 } });")
        lines.append("          addGeoJson('Forest loss since 2020', config.layers.forest_loss_post_2020, { style: { color: '#c62828', weight: 1, fillOpacity: 0.4 } });")
        lines.append("          addGeoJson('AOI boundary', config.layers.aoi_boundary, { style: { color: '#1976d2', weight: 2, fillOpacity: 0 } });")
        lines.append("          addGeoJson('Maa-amet parcels', config.layers.parcels, {")
        lines.append("            style: { color: '#6a1b9a', weight: 1, fillOpacity: 0.05 },")
        lines.append("            onEachFeature: (feature, layer) => {")
        lines.append("              const props = feature.properties || {};")
        lines.append("              const label = `${props.parcel_id || ''} | forest_ha=${props.hansen_forest_area_ha ?? ''} | loss_ha=${props.hansen_forest_loss_ha ?? ''}`;")
        lines.append("              layer.bindTooltip(label, { sticky: true });")
        lines.append("            },")
        lines.append("          });")
        lines.append("          L.control.layers(baseLayers, overlays, { collapsed: false }).addTo(map);")
        lines.append("        });")
        lines.append("    })();")
        lines.append("  </script>")

    lines.append("  <h2>Assumptions & Limitations</h2>")
    if not assumptions:
        lines.append("  <p><strong>No assumptions declared in this report.</strong></p>")
    else:
        lines.append("  <table>")
        lines.append("    <tr><th>Assumption</th><th>Testable</th><th>Affected results</th></tr>")
        result_ids = {anchor_id("result", r.get("result_id")) for r in results or [] if isinstance(r, dict) and r.get("result_id") is not None}

        def result_link_or_error(result_id: Any) -> str:
            if result_id is None:
                return "<strong>missing</strong>"
            anchor = anchor_id("result", result_id)
            if anchor in result_ids:
                return f"<a href=\"#{html.escape(anchor)}\">{html.escape(str(result_id))}</a>"
            return f"<strong>missing-link</strong> {html.escape(str(result_id))}"

        if isinstance(assumptions, list):
            for entry in assumptions:
                if isinstance(entry, dict):
                    text = entry.get("text") or entry.get("assumption") or entry.get("statement")
                    testable = entry.get("testable")
                    affected = entry.get("affected_results") or entry.get("results") or []
                    assumption_text = json.dumps(text, sort_keys=True, ensure_ascii=False) if text is not None else json.dumps(entry, sort_keys=True, ensure_ascii=False)
                    testable_text = "" if testable is None else str(testable)
                    if testable is False:
                        testable_text = f"{testable_text} (not testable)"
                    if isinstance(affected, list):
                        affected_links = ", ".join(result_link_or_error(rid) for rid in affected) if affected else "<strong>missing</strong>"
                    else:
                        affected_links = result_link_or_error(affected)
                    lines.append(
                        "    <tr>"
                        f"<td><code>{html.escape(assumption_text)}</code></td>"
                        f"<td>{html.escape(testable_text)}</td>"
                        f"<td>{affected_links}</td>"
                        "</tr>"
                    )
                else:
                    value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                    lines.append(
                        "    <tr>"
                        f"<td><code>{html.escape(value)}</code></td>"
                        "<td></td>"
                        "<td><strong>missing</strong></td>"
                        "</tr>"
                    )
        else:
            value = json.dumps(assumptions, sort_keys=True, ensure_ascii=False)
            lines.append(
                "    <tr>"
                f"<td><code>{html.escape(value)}</code></td>"
                "<td></td>"
                "<td><strong>missing</strong></td>"
                "</tr>"
            )
        lines.append("  </table>")
    lines.append("  <div style=\"height:12px;\"></div>")

    lines.append("  <h2>Results</h2>")
    if not results:
        lines.append("  <p><em>No results declared.</em></p>")
    else:
        lines.append("  <table>")
        lines.append("    <tr><th>Result</th><th>Status</th><th>Criteria</th></tr>")
        if isinstance(results, list):
            for entry in results:
                if not isinstance(entry, dict):
                    value = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                    lines.append(
                        "    <tr>"
                        f"<td colspan=\"3\"><code>{html.escape(value)}</code></td>"
                        "</tr>"
                    )
                    continue
                result_id = entry.get("result_id")
                status = entry.get("status")
                criteria_ids = entry.get("criteria_ids") or []
                result_anchor = anchor_id("result", result_id)
                criteria_links = []
                for cid in criteria_ids:
                    criteria_links.append(f"<a href=\"#{html.escape(anchor_id('criteria', cid))}\">{html.escape(str(cid))}</a>")
                criteria_html = ", ".join(criteria_links) if criteria_links else ""
                lines.append(
                    "    <tr>"
                    f"<td id=\"{html.escape(result_anchor)}\">{html.escape(str(result_id))}</td>"
                    f"<td>{html.escape(str(status)) if status is not None else ''}</td>"
                    f"<td>{criteria_html}</td>"
                    "</tr>"
                )
        else:
            value = json.dumps(results, sort_keys=True, ensure_ascii=False)
            lines.append(
                "    <tr>"
                f"<td colspan=\"3\"><code>{html.escape(value)}</code></td>"
                "</tr>"
            )
        lines.append("  </table>")
    lines.append("  <div style=\"height:12px;\"></div>")

    lines.append("  <h2>Evidence Artifacts</h2>")
    lines.append("  <ul>")
    for entry in evidence_sorted:
        relpath = str(entry.get("relpath", ""))
        if not relpath:
            continue
        href = html.escape(relpath_from_html(run_dir, html_path, relpath))
        label = html.escape(relpath)
        lines.append(f"    <li><a href=\"{href}\">{label}</a></li>")
    lines.append("  </ul>")

    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"


def render_run_report_html(report: dict[str, Any], run_dir: Path, report_json_name: str = "aoi_report.json") -> str:
    aoi_id = str(report.get("aoi_id", ""))
    bundle_id = str(report.get("bundle_id", ""))
    generated = str(report.get("generated_at_utc", ""))
    html_path = run_dir / "report.html"
    map_assets = report.get("map_assets") if isinstance(report.get("map_assets"), dict) else None

    report_metadata = report.get("report_metadata") or {}
    regulatory_context = {}
    if isinstance(report_metadata, dict):
        regulatory_context = report_metadata.get("regulatory_context") or {}

    results = report.get("results") or []
    evidence = report.get("evidence_artifacts") or []

    def _find_relpath(suffix: str) -> str | None:
        for entry in evidence:
            relpath = entry.get("relpath", "") if isinstance(entry, dict) else ""
            if relpath.endswith(suffix):
                return relpath
        return None

    html_relpath = find_html_relpath(report)
    report_json_relpath = _find_relpath(f"{aoi_id}.json") or _find_relpath(".json") or ""
    metrics_relpath = _find_relpath(f"{aoi_id}/metrics.csv") or _find_relpath("metrics.csv") or ""
    aoi_geojson_relpath = report.get("aoi_geometry_ref", {}).get("value", "")

    core_links: list[tuple[str, str]] = [
        (report_json_name, report_json_name),
        (f"reports/{report.get('report_version', 'aoi_report_v1')}/{aoi_id}.html", html_relpath),
        (f"reports/{report.get('report_version', 'aoi_report_v1')}/{aoi_id}.json", report_json_relpath),
        (f"reports/{report.get('report_version', 'aoi_report_v1')}/{aoi_id}/metrics.csv", metrics_relpath),
        ("inputs/aoi.geojson", aoi_geojson_relpath),
    ]
    deduped_links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, relpath in core_links:
        if not relpath or relpath in seen:
            continue
        seen.add(relpath)
        deduped_links.append((label, relpath))

    evidence_sorted = sorted(
        [entry for entry in evidence if isinstance(entry, dict)],
        key=lambda item: str(item.get("relpath", "")),
    )

    status_map: dict[str, list[str]] = {}
    for entry in results:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", ""))
        result_id = str(entry.get("result_id", ""))
        if not status:
            status = "unknown"
        status_map.setdefault(status, []).append(result_id)

    computed_results = sorted(status_map.get("computed", []))
    placeholder_results = sorted(status_map.get("placeholder", []))
    other_statuses = sorted(
        [
            f"{status}: {', '.join(sorted(ids)) or '(none)'}"
            for status, ids in status_map.items()
            if status not in {"computed", "placeholder"}
        ]
    )

    gaps: list[str] = []
    for dep in report.get("external_dependencies", []) or []:
        if not isinstance(dep, dict):
            continue
        if dep.get("tile_source") != "local":
            continue
        missing_tiles: list[str] = []
        for tile in dep.get("tiles_used", []) or []:
            if not isinstance(tile, dict):
                continue
            if str(tile.get("source_url", "")).strip():
                continue
            tile_id = str(tile.get("tile_id", ""))
            layer = str(tile.get("layer", ""))
            missing_tiles.append(f"{tile_id}:{layer}")
        if missing_tiles:
            missing_tiles = sorted(set(missing_tiles))
            gaps.append(
                "Missing tile source URLs in external_dependencies.tiles_used: "
                + ", ".join(missing_tiles)
            )

    crosscheck = report.get("validation", {}).get("forest_area_crosscheck", {})
    if isinstance(crosscheck, dict):
        outcome = crosscheck.get("outcome")
        reason = crosscheck.get("reason")
        if outcome == "not_comparable":
            gaps.append(f"Maa-amet crosscheck not comparable: {reason or 'reason_not_declared'}")

    in_scope = []
    if isinstance(regulatory_context, dict):
        in_scope = regulatory_context.get("in_scope_articles") or []
    if not in_scope:
        gaps.append("regulatory_context.in_scope_articles is empty")

    policy_refs = report.get("policy_mapping_refs") or []
    if not policy_refs:
        gaps.append("policy_mapping_refs is empty")

    gaps = sorted(dict.fromkeys(gaps))

    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append('<html lang="en">')
    lines.append("<head>")
    lines.append("  <meta charset=\"utf-8\" />")
    lines.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />")
    lines.append(f"  <title>AOI Report — {html.escape(aoi_id)}</title>")
    lines.append("  <style>")
    lines.append("    :root { --fg:#111; --bg:#fff; --muted:#666; --card:#f6f7f9; --link:#0b5fff; }")
    lines.append("    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;")
    lines.append("           color: var(--fg); background: var(--bg); margin: 0; }")
    lines.append("    header { border-bottom: 1px solid #e7e7e7; background: #fff; position: sticky; top: 0; }")
    lines.append("    .wrap { max-width: 980px; margin: 0 auto; padding: 16px 20px; }")
    lines.append("    nav a { margin-right: 14px; text-decoration: none; color: var(--link); font-weight: 600; }")
    lines.append("    nav a.active { color: var(--fg); }")
    lines.append("    main { padding: 18px 20px 40px; }")
    lines.append("    h1 { margin: 0 0 6px; font-size: 22px; }")
    lines.append("    p { line-height: 1.5; }")
    lines.append("    .muted { color: var(--muted); }")
    lines.append("    .card { background: var(--card); border: 1px solid #e8eaee; border-radius: 12px; padding: 14px 14px; }")
    lines.append("    ul { padding-left: 18px; }")
    lines.append("    code { background: #f1f1f1; padding: 1px 4px; border-radius: 6px; }")
    lines.append("    #map { height: 420px; border: 1px solid #ddd; border-radius: 8px; margin: 12px 0 16px; background: #fafafa; }")
    lines.append("  </style>")
    if map_assets and map_assets.get("config_relpath"):
        lines.append(
            "  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" "
            "integrity=\"sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=\" crossorigin=\"\" />"
        )
        lines.append(
            "  <script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\" "
            "integrity=\"sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=\" crossorigin=\"\"></script>"
        )
    lines.append("</head>")
    lines.append("<body>")
    lines.append("  <header>")
    lines.append("    <div class=\"wrap\">")
    lines.append("      <nav>")
    lines.append("        <a href=\"../../../index.html\">Home</a>")
    lines.append("        <a href=\"../../../articles/index.html\">Articles</a>")
    lines.append("        <a href=\"../../../dependencies/index.html\">Dependencies</a>")
    lines.append("        <a href=\"../../../regulation/links.html\">Regulation</a>")
    lines.append("        <a href=\"../../../regulation/sources.html\">Sources</a>")
    lines.append("        <a href=\"../../../regulation/policy_to_evidence_spine.html\">Spine</a>")
    lines.append("        <a href=\"../../../views/index.html\">Views</a>")
    lines.append("        <a href=\"../../index.html\" class=\"active\">AOI Reports</a>")
    lines.append("        <a href=\"../../../dao_stakeholders/index.html\">DAO (Stakeholders)</a>")
    lines.append("        <a href=\"../../../dao_dev/index.html\">DAO (Developers)</a>")
    lines.append("      </nav>")
    lines.append("    </div>")
    lines.append("  </header>")
    lines.append("  <main>")
    lines.append("    <div class=\"wrap\">")
    lines.append("      <p class=\"muted\"><a href=\"../../index.html\">Back to AOI runs</a></p>")
    lines.append("      <h1>AOI Report</h1>")
    lines.append(
        "      <p><b>AOI</b>: <code>"
        + html.escape(aoi_id)
        + "</code><br />\n"
        + "         <b>Bundle</b>: <code>"
        + html.escape(bundle_id)
        + "</code><br />\n"
        + "         <b>Generated (UTC)</b>: <code>"
        + html.escape(generated)
        + "</code></p>"
    )

    lines.append("      <div class=\"card\">")
    lines.append("        <h2>Core inspection artifacts</h2>")
    lines.append("        <ul>")
    for label, relpath in deduped_links:
        href = html.escape(relpath_from_html(run_dir, html_path, relpath))
        lines.append(f"          <li><a href=\"{href}\">{html.escape(relpath)}</a> ({html.escape(label)})</li>")
    lines.append("        </ul>")
    lines.append("        <p class=\"muted\">If a manifest is present in this bundle, it should also be linked from this page.</p>")
    lines.append("      </div>")

    lines.append(render_post2020_overview_card(report))

    if map_assets and map_assets.get("config_relpath"):
        map_config_relpath = str(map_assets.get("config_relpath"))
        map_href = html.escape(relpath_from_html(run_dir, html_path, map_config_relpath))
        lines.append("      <div class=\"card\">")
        lines.append("        <h2>Map (interactive)</h2>")
        lines.append(f"        <p><a href=\"{map_href}\">map_config.json</a></p>")
        lines.append("        <div id=\"map\"></div>")
        lines.append("        <script>")
        lines.append("          (function () {")
        lines.append("            const map = L.map('map', { zoomControl: true });")
        lines.append("            const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {")
        lines.append("              attribution: 'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',")
        lines.append("            }).addTo(map);")
        lines.append(f"            const configUrl = '{map_href}';")
        lines.append("            fetch(configUrl)")
        lines.append("              .then((resp) => resp.json())")
        lines.append("              .then((config) => {")
        lines.append("                const bbox = config.aoi_bbox;")
        lines.append("                const bounds = L.latLngBounds([")
        lines.append("                  [bbox.min_lat, bbox.min_lon],")
        lines.append("                  [bbox.max_lat, bbox.max_lon],")
        lines.append("                ]);")
        lines.append("                map.fitBounds(bounds);")
        lines.append("                const overlays = {};")
        lines.append("                const baseLayers = { Satellite: satellite };")
        lines.append("                const addGeoJson = (label, url, options) => {")
        lines.append("                  if (!url) return;")
        lines.append("                  fetch(url)")
        lines.append("                    .then((r) => r.json())")
        lines.append("                    .then((data) => {")
        lines.append("                      const layer = L.geoJSON(data, options).addTo(map);")
        lines.append("                      overlays[label] = layer;")
        lines.append("                    });")
        lines.append("                };")
        lines.append("                addGeoJson('Forest cover 2000', config.layers.forest_2000, { style: { color: '#2e7d32', weight: 1, fillOpacity: 0.3 } });")
        lines.append("                addGeoJson(`Forest cover ${config.latest_year}`, config.layers.forest_end_year, { style: { color: '#1b5e20', weight: 1, fillOpacity: 0.3 } });")
        lines.append("                addGeoJson('Forest loss since 2020', config.layers.forest_loss_post_2020, { style: { color: '#c62828', weight: 1, fillOpacity: 0.4 } });")
        lines.append("                addGeoJson('AOI boundary', config.layers.aoi_boundary, { style: { color: '#1976d2', weight: 2, fillOpacity: 0 } });")
        lines.append("                addGeoJson('Maa-amet parcels', config.layers.parcels, {")
        lines.append("                  style: { color: '#6a1b9a', weight: 1, fillOpacity: 0.05 },")
        lines.append("                  onEachFeature: (feature, layer) => {")
        lines.append("                    const props = feature.properties || {};")
        lines.append("                    const label = `${props.parcel_id || ''} | forest_ha=${props.hansen_forest_area_ha ?? ''} | loss_ha=${props.hansen_forest_loss_ha ?? ''}`;")
        lines.append("                    layer.bindTooltip(label, { sticky: true });")
        lines.append("                  },")
        lines.append("                });")
        lines.append("                L.control.layers(baseLayers, overlays, { collapsed: false }).addTo(map);")
        lines.append("              });")
        lines.append("          })();")
        lines.append("        </script>")
        lines.append("      </div>")

    lines.append("      <div class=\"card\">")
    lines.append("        <h2>What this example demonstrates</h2>")
    lines.append("        <ul>")
    lines.append(
        "          <li>Inspectable artifacts with links + hashes ("
        + str(len(evidence_sorted))
        + f" declared in <code>{html.escape(report_json_name)}</code>).</li>"
    )
    lines.append("          <li>Computed vs placeholder results are declared in <code>results[].status</code>.</li>")
    if computed_results:
        lines.append(
            "          <li>Computed results: <code>"
            + html.escape(", ".join(computed_results))
            + "</code>.</li>"
        )
    if placeholder_results:
        lines.append(
            "          <li>Placeholder results: <code>"
            + html.escape(", ".join(placeholder_results))
            + "</code>.</li>"
        )
    if other_statuses:
        lines.append(
            "          <li>Other status values: <code>"
            + html.escape("; ".join(other_statuses))
            + "</code>.</li>"
        )
    lines.append("          <li>Inspection shows declared evidence, not certification or compliance.</li>")
    lines.append("        </ul>")
    lines.append("      </div>")

    lines.append("      <div class=\"card\">")
    lines.append("        <h2>Known evidence gaps (for DAO)</h2>")
    if gaps:
        lines.append("        <ul>")
        for gap in gaps:
            lines.append(f"          <li>{html.escape(gap)}</li>")
        lines.append("        </ul>")
    else:
        lines.append(
            "        <p class=\"muted\">No gaps detected from <code>"
            + html.escape(report_json_name)
            + "</code>.</p>"
        )
    lines.append("      </div>")

    lines.append("      <div class=\"card\">")
    lines.append("        <h2>Declared evidence artifacts</h2>")
    lines.append("        <ul>")
    for entry in evidence_sorted:
        relpath = str(entry.get("relpath", ""))
        if not relpath:
            continue
        href = html.escape(relpath_from_html(run_dir, run_dir / "report.html", relpath))
        lines.append(f"          <li><a href=\"{href}\">{html.escape(relpath)}</a></li>")
    lines.append("        </ul>")
    lines.append("      </div>")

    lines.append("    </div>")
    lines.append("  </main>")
    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256_hex(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def render_aoi_run(run_dir: Path, report_json_name: str = "aoi_report.json") -> RenderedArtifacts:
    report_path = run_dir / report_json_name
    report = load_report(report_path)

    html_relpath = find_html_relpath(report)
    json_relpath = find_artifact_relpath(report, ".json")
    metrics_relpath = find_artifact_relpath(report, "metrics.csv")

    html_content = render_report_html(report, run_dir, html_relpath)
    report_json_content = render_report_json(report)
    metrics_csv_content = render_metrics_csv(report)

    write_text(run_dir / html_relpath, html_content)
    write_text(run_dir / json_relpath, report_json_content)
    write_text(run_dir / metrics_relpath, metrics_csv_content)
    write_text(run_dir / "report.html", render_run_report_html(report, run_dir, report_json_name=report_json_name))

    return RenderedArtifacts(
        html_relpath=html_relpath,
        json_relpath=json_relpath,
        metrics_relpath=metrics_relpath,
    )


def update_evidence_hashes(run_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    updates = {}
    for entry in report.get("evidence_artifacts", []):
        relpath = entry.get("relpath")
        if not relpath:
            continue
        artifact_path = run_dir / relpath
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Missing declared artefact: {artifact_path}")
        entry["sha256"] = sha256_hex(artifact_path)
        entry["size_bytes"] = artifact_path.stat().st_size
        updates[relpath] = entry
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_runs(runs_dir: Path) -> Iterable[Path]:
    for entry in sorted(runs_dir.iterdir()):
        if entry.is_dir():
            yield entry
