#!/usr/bin/env python3
"""Generate a Sample Report (EUDR Compliance Report) from a DAO Evidence Bundle.

Usage:
  python3 scripts/generate_sample_report_from_bundle.py \
    --bundle-dir docs/site/bundles/runs/west_africa \
    --output-dir docs/site/sample_reports/runs/demo_2026-03-08/demo_plot_01 \
    --report-json west_africa_aoi_report.json
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from aoi_report_renderer import (  # noqa: E402
    render_report_html_static,
    render_report_json,
    render_static_map_image,
    sha256_hex,
)


KNOWN_OUTPUT_ARTIFACTS = {
    "report.html",
    "report.json",
    "report.pdf",
    "manifest.sha256",
    "deforestation_map.svg",
    "deforestation_map.png",
    "deforestation_map_satellite.png",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _looks_like_report_manifest(payload: dict[str, Any]) -> bool:
    return bool(payload.get("aoi_id")) and isinstance(payload.get("evidence_artifacts"), list)


def _resolve_report_json_path(bundle_dir: Path, preferred_name: str) -> Path:
    preferred_path = bundle_dir / preferred_name
    if preferred_path.is_file():
        return preferred_path

    fallback_path = bundle_dir / "aoi_report.json"
    if fallback_path.is_file():
        return fallback_path

    for candidate in sorted(bundle_dir.glob("*.json")):
        if candidate.name in {"summary.json", "manifest.json"}:
            continue
        try:
            payload = _load_json(candidate)
        except Exception:
            continue
        if _looks_like_report_manifest(payload):
            return candidate

    raise FileNotFoundError(
        f"Could not resolve report JSON in {bundle_dir} (preferred: {preferred_name})"
    )


def _rewrite_bundle_relative_links(
    html_content: str,
    *,
    bundle_html_dir: Path,
    output_dir: Path,
    local_hrefs: set[str],
) -> str:
    href_pattern = re.compile(r'href="([^"]+)"')

    def replace_href(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith(("#", "http://", "https://", "mailto:", "data:")):
            return match.group(0)
        if href in local_hrefs:
            return match.group(0)
        target_path = (bundle_html_dir / href).resolve()
        rewritten = Path(os.path.relpath(target_path, output_dir)).as_posix()
        return f'href="{html.escape(rewritten, quote=True)}"'

    return href_pattern.sub(replace_href, html_content)


def _insert_footer(
    html_content: str,
    *,
    source_bundle_href: str,
    artifact_names: list[str],
) -> str:
    artifact_links = " · ".join(
        f'<a href="{html.escape(name, quote=True)}">{html.escape(name)}</a>' for name in artifact_names
    )
    footer_html = (
        "\n  <footer style=\"margin-top: 24px; padding-top: 16px; border-top: 1px solid #ddd; color: #444;\">"
        f"\n    <p><strong>Source Bundle:</strong> <a href=\"{html.escape(source_bundle_href, quote=True)}\">report.html</a></p>"
        f"\n    <p><strong>Sample artifacts:</strong> {artifact_links}</p>"
        "\n  </footer>\n"
    )
    return html_content.replace("</body>", f"{footer_html}</body>", 1)


def _write_manifest(output_dir: Path, artifact_names: list[str]) -> None:
    lines = [
        f"{sha256_hex(output_dir / artifact_name)}  {artifact_name}"
        for artifact_name in artifact_names
        if (output_dir / artifact_name).is_file()
    ]
    (output_dir / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _to_pdf_safe_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def _wrap_pdf_line(value: str, max_chars: int = 88) -> list[str]:
    words = value.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        lines.append(current)
        current = word

    lines.append(current)
    return lines


def _write_minimal_pdf(lines: list[str], pdf_path: Path) -> None:
    lines_per_page = 44
    pages = [lines[index:index + lines_per_page] for index in range(0, len(lines), lines_per_page)]
    if not pages:
        pages = [[""]]

    objects: dict[int, str] = {}
    objects[1] = "<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{4 + page_index * 2} 0 R" for page_index in range(len(pages)))
    objects[2] = f"<< /Type /Pages /Count {len(pages)} /Kids [{kids}] >>"
    objects[3] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    for page_index, page_lines in enumerate(pages):
        page_object_id = 4 + page_index * 2
        content_object_id = page_object_id + 1
        stream = "\n".join(
            [
                "BT",
                "/F1 11 Tf",
                "48 780 Td",
                "14 TL",
                *[f"({_to_pdf_safe_text(line)}) Tj T*" for line in page_lines],
                "ET",
            ]
        )
        objects[page_object_id] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_object_id} 0 R >>"
        )
        objects[content_object_id] = (
            f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream"
        )

    pdf = "%PDF-1.4\n"
    offsets = {0: 0}

    for object_id in sorted(objects):
        offsets[object_id] = len(pdf.encode("utf-8"))
        pdf += f"{object_id} 0 obj\n{objects[object_id]}\nendobj\n"

    xref_offset = len(pdf.encode("utf-8"))
    pdf += f"xref\n0 {max(objects) + 1}\n"
    pdf += "0000000000 65535 f \n"
    for object_id in range(1, max(objects) + 1):
        offset = offsets.get(object_id, 0)
        pdf += f"{offset:010d} 00000 n \n"
    pdf += f"trailer\n<< /Size {max(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    pdf_path.write_bytes(pdf.encode("utf-8"))


def _maybe_render_pdf_from_html(html_path: Path, pdf_path: Path) -> bool:
    try:
        from weasyprint import HTML  # type: ignore

        HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
        return True
    except Exception:
        pass

    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
    except Exception:
        text = html.unescape(re.sub(r"<[^>]+>", "\n", html_path.read_text(encoding="utf-8")))
        lines = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            lines.extend(_wrap_pdf_line(stripped))
        _write_minimal_pdf(lines, pdf_path)
        return pdf_path.is_file()

    text = html.unescape(re.sub(r"<[^>]+>", "\n", html_path.read_text(encoding="utf-8")))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    page_width, page_height = A4
    x = 40
    y = page_height - 40
    c.setFont("Helvetica", 10)
    for line in lines:
        wrapped = line
        while wrapped:
            segment = wrapped[:105]
            wrapped = wrapped[105:]
            c.drawString(x, y, segment)
            y -= 14
            if y < 40:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = page_height - 40
    c.save()
    return pdf_path.is_file()


def _clear_previous_outputs(output_dir: Path) -> None:
    for artifact_name in sorted(KNOWN_OUTPUT_ARTIFACTS):
        artifact_path = output_dir / artifact_name
        if artifact_path.is_file():
            artifact_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a sample EUDR compliance report from a bundle AOI report."
    )
    parser.add_argument("--bundle-dir", required=True, help="Path to bundle run directory")
    parser.add_argument("--output-dir", required=True, help="Path to sample report output directory")
    parser.add_argument(
        "--report-json",
        default="aoi_report.json",
        help="Bundle report JSON filename (falls back to the detected AOI report manifest)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    bundle_dir = Path(args.bundle_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    report_json_path = _resolve_report_json_path(bundle_dir, args.report_json)
    report = _load_json(report_json_path)

    map_assets = report.get("map_assets") if isinstance(report.get("map_assets"), dict) else None
    if not map_assets:
        raise SystemExit(f"Report JSON has no map_assets config: {report_json_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    _clear_previous_outputs(output_dir)

    static_map = render_static_map_image(
        run_dir=bundle_dir,
        map_assets=map_assets,
        output_dir=output_dir,
    )

    bundle_html_relpath = next(
        str(entry.get("relpath", ""))
        for entry in report.get("evidence_artifacts", [])
        if str(entry.get("relpath", "")).endswith(".html")
    )
    html_content = render_report_html_static(
        report,
        bundle_dir,
        bundle_html_relpath,
        static_map_png_relpath=static_map.png_relpath,
        static_map_svg_relpath=static_map.svg_relpath,
    )

    local_hrefs = {
        "report.html",
        "report.json",
        "report.pdf",
        "manifest.sha256",
        static_map.svg_relpath,
        static_map.png_relpath,
    }
    if static_map.satellite_png_relpath:
        local_hrefs.add(static_map.satellite_png_relpath)

    bundle_html_dir = (bundle_dir / bundle_html_relpath).parent
    html_content = _rewrite_bundle_relative_links(
        html_content,
        bundle_html_dir=bundle_html_dir,
        output_dir=output_dir,
        local_hrefs=local_hrefs,
    )
    source_bundle_href = Path(os.path.relpath(bundle_dir / "report.html", output_dir)).as_posix()

    artifact_names = ["report.json", "report.html", static_map.svg_relpath, static_map.png_relpath]
    if static_map.satellite_png_relpath:
        artifact_names.append(static_map.satellite_png_relpath)

    report_html_path = output_dir / "report.html"
    report_json_output_path = output_dir / "report.json"
    report_html_path.write_text(
        _insert_footer(
            html_content,
            source_bundle_href=source_bundle_href,
            artifact_names=artifact_names + ["manifest.sha256"],
        ),
        encoding="utf-8",
    )
    report_json_output_path.write_text(render_report_json(report), encoding="utf-8")

    report_pdf_path = output_dir / "report.pdf"
    if _maybe_render_pdf_from_html(report_html_path, report_pdf_path):
        artifact_names.insert(2, "report.pdf")

    _write_manifest(output_dir, artifact_names)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
