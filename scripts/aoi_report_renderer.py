#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class RenderedArtifacts:
    html_relpath: str
    json_relpath: str
    metrics_relpath: str


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


def render_run_report_html(report: dict[str, Any], run_dir: Path) -> str:
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
        ("aoi_report.json", "aoi_report.json"),
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
        + " declared in <code>aoi_report.json</code>).</li>"
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
        lines.append("        <p class=\"muted\">No gaps detected from <code>aoi_report.json</code>.</p>")
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


def render_aoi_run(run_dir: Path) -> RenderedArtifacts:
    report_path = run_dir / "aoi_report.json"
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
    write_text(run_dir / "report.html", render_run_report_html(report, run_dir))

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
