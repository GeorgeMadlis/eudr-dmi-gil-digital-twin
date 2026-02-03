#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from site_nav import render_header_nav  # noqa: E402


def render_runs(runs_dir: Path) -> str:
  example_dir = runs_dir / "example"
  if not example_dir.is_dir():
    return "<li><em>No example report found.</em></li>"

  report_href = "runs/example/report.html"
  summary_path = example_dir / "summary.json"
  if summary_path.is_file():
    summary_href = "runs/example/summary.json"
    return (
      "<li>"
      f"<a href=\"{report_href}\">example</a> "
      "<span class=\"muted\">(</span>"
      f"<a href=\"{summary_href}\">summary.json</a>"
      "<span class=\"muted\">)</span>"
      "</li>"
    )

  return f"<li><a href=\"{report_href}\">example</a></li>"


def build_page(*, runs_dir: Path) -> str:
    header_html = render_header_nav(rel_prefix="../", active_label="AOI Reports")
    runs_html = render_runs(runs_dir)
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>AOI Reports</title>
    <style>
      :root {{ --fg:#111; --bg:#fff; --muted:#666; --card:#f6f7f9; --link:#0b5fff; }}
      body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
             color: var(--fg); background: var(--bg); margin: 0; }}
      header {{ border-bottom: 1px solid #e7e7e7; background: #fff; position: sticky; top: 0; }}
      .wrap {{ max-width: 980px; margin: 0 auto; padding: 16px 20px; }}
      nav a {{ margin-right: 14px; text-decoration: none; color: var(--link); font-weight: 600; }}
      nav a.active {{ color: var(--fg); }}
      main {{ padding: 18px 20px 40px; }}
      h1 {{ margin: 0 0 6px; font-size: 22px; }}
      h2 {{ margin-top: 24px; font-size: 18px; }}
      p {{ line-height: 1.5; }}
      .muted {{ color: var(--muted); }}
      .card {{ background: var(--card); border: 1px solid #e8eaee; border-radius: 12px; padding: 14px 14px; }}
      ul {{ padding-left: 18px; }}
      code {{ background: #f1f1f1; padding: 1px 4px; border-radius: 6px; }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; }}
      @media (min-width: 760px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
    </style>
  </head>
  <body>
    {header_html}
    <main>
      <div class=\"wrap\">
        <!-- Generated from docs/site/aoi_reports/runs/ -->
<h1>AOI Reports</h1>
<p class=\"muted\">Portable mode: links point into the bundle under <code>runs/&lt;run_id&gt;/report.html</code>.</p>
<p class=\"muted\">This page shows a single AOI-agnostic example report. It is overwritten on each publish; older versions remain available via git history but are not exposed in the portal.</p>
<div class=\"notice\" style=\"border:1px solid #ddd; padding:12px; border-radius:8px; margin:12px 0;\">
  <strong>AI/automation inspection note (mandatory):</strong>
  <ul style=\"margin:8px 0 0 18px;\">
    <li><strong>Do not infer or construct report URLs from run IDs.</strong></li>
    <li>Access reports only by clicking through the portal: <em>Home → AOI Reports → Run entry → report.html → linked JSON artefacts</em>.</li>
    <li>If a listed artefact cannot be opened via this click-path, record it as an <strong>Evidence gap — published artefact is inaccessible via inspection surface</strong>.</li>
  </ul>
  <div style=\"margin-top:8px;\">
    See: <a href=\"../dte_instructions.html\">DTE Instructions v1.1</a>
  </div>
</div>
<div class=\"card\">
  <h2>Runs (newest first)</h2>
  <ul>
{runs_html}
  </ul>
</div>
      </div>
    </main>
    <footer style=\"border-top:1px solid #e7e7e7; background:#fff;\">
      <div style=\"max-width:980px; margin:0 auto; padding:18px 20px 28px; color:#666; font-size:13px;\">
        <a href=\"../privacy.html\" style=\"color:#0b5fff; text-decoration:none; font-weight:600;\">Privacy Policy</a>
        <span style=\"margin:0 8px; color:#999;\">|</span>
        <a href=\"../dte_instructions.html\" style=\"color:#0b5fff; text-decoration:none; font-weight:600;\">DTE Instructions v1.1</a>
      </div>
    </footer>
  </body>
</html>
"""


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild AOI reports index from docs/site/aoi_reports/runs/.")
    p.add_argument("--site-root", default="docs/site", help="Root folder containing site HTML")
    args = p.parse_args()

    site_root = Path(args.site_root)
    runs_dir = site_root / "aoi_reports" / "runs"
    if not runs_dir.is_dir():
        raise SystemExit(f"Runs dir not found: {runs_dir}")

    out_path = site_root / "aoi_reports" / "index.html"
    out_path.write_text(build_page(runs_dir=runs_dir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
