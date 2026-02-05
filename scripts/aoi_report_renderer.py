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

    inputs = report.get("inputs", {}).get("sources", [])
    inputs_sorted = sorted(inputs, key=lambda item: str(item.get("source_id", "")))

    evidence = report.get("evidence_artifacts", [])
    evidence_sorted = sorted(evidence, key=lambda item: str(item.get("relpath", "")))

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
    lines.append("  </style>")
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
        if isinstance(evidence_registry, list):
            for entry in evidence_registry:
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
                evidence_class = entry.get("class") or entry.get("evidence_class") or entry.get("id")
                mandatory = entry.get("mandatory")
                status = entry.get("status")
                status_text = "" if status is None else str(status)
                mandatory_text = "" if mandatory is None else str(mandatory)
                is_missing = bool(mandatory is True and status_text.lower() in {"missing", "absent", "unavailable", "not_found"})
                row_style = " style=\"background:#fff5f5; border-left:4px solid #b00020;\"" if is_missing else ""
                lines.append(
                    f"    <tr{row_style}>"
                    f"<td>{html.escape(str(evidence_class))}</td>"
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
    lines.append("    <tr><th>Metric</th><th>Value</th><th>Unit</th><th>Notes</th><th>Source</th></tr>")
    for row in render_metrics_rows(report):
        lines.append(
            "    <tr>"
            f"<td>{html.escape(row['variable'])}</td>"
            f"<td>{html.escape(row['value'])}</td>"
            f"<td>{html.escape(row['unit'])}</td>"
            f"<td>{html.escape(row['notes'])}</td>"
            f"<td>{html.escape(row['source'])}</td>"
            "</tr>"
        )
    lines.append("  </table>")

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
