#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from site_nav import render_header_nav


HEADER_RE = re.compile(r"<header>.*?</header>", re.DOTALL)
BODY_RE = re.compile(r"<body(\s[^>]*)?>", re.IGNORECASE)


def replace_or_insert_header(html: str, header_html: str) -> str:
    if HEADER_RE.search(html):
        return HEADER_RE.sub(header_html, html, count=1)

    # Insert header right after <body> tag.
    match = BODY_RE.search(html)
    if not match:
        raise ValueError("No <body> tag found in HTML")

    insert_at = match.end()
    return html[:insert_at] + "\n  " + header_html + html[insert_at:]


def rebuild_file(path: Path, *, rel_prefix: str, active_label: str | None) -> None:
    html = path.read_text(encoding="utf-8")
    header_html = render_header_nav(rel_prefix=rel_prefix, active_label=active_label)
    updated = replace_or_insert_header(html, header_html)
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild site header/nav with correct rel_prefix.")
    p.add_argument("--site-root", default="docs/site", help="Root folder containing site HTML")
    p.add_argument("--run-id", required=True, help="AOI run id to update (runs/<run_id>/report.html)")
    args = p.parse_args()

    site_root = Path(args.site_root)

    rebuild_file(site_root / "index.html", rel_prefix="", active_label="Home")
    rebuild_file(site_root / "aoi_reports" / "index.html", rel_prefix="../", active_label="AOI Reports")
    rebuild_file(
        site_root / "aoi_reports" / "runs" / args.run_id / "report.html",
        rel_prefix="../../../",
        active_label="AOI Reports",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
