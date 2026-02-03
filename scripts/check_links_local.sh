#!/usr/bin/env bash
set -euo pipefail

SITE_ROOT_DEFAULT="docs/site"
SITE_ROOT="$SITE_ROOT_DEFAULT"

usage() {
  cat <<EOF
Usage: scripts/check_links_local.sh [--site-root docs/site]

Checks local links in:
- docs/site/index.html
- docs/site/aoi_reports/index.html

Exits non-zero on failure.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site-root)
      SITE_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -d "$SITE_ROOT" ]]; then
  echo "ERROR: site root not found: $SITE_ROOT" >&2
  exit 2
fi

python3 - "$SITE_ROOT" <<'PY'
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

site_root = Path(sys.argv[1]).resolve()
paths = [site_root / "index.html", site_root / "aoi_reports" / "index.html"]

class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for k, v in attrs:
            if v is None:
                continue
            if k in {"href", "src"}:
                self.links.append(v)


def is_ignored(url: str) -> bool:
    u = url.strip()
    if not u:
        return True
    if u.startswith("#"):
        return True
    u_lower = u.lower()
    return any(u_lower.startswith(p) for p in ("http://", "https://", "mailto:", "tel:"))


def strip_fragment(url: str) -> str:
    if "#" in url:
        url = url.split("#", 1)[0]
    if "?" in url:
        url = url.split("?", 1)[0]
    return url


broken: list[str] = []
scanned = 0

for html_path in paths:
    if not html_path.is_file():
        broken.append(f"missing page: {html_path}")
        continue

    scanned += 1
    parser = LinkExtractor()
    parser.feed(html_path.read_text(encoding="utf-8", errors="replace"))

    for link in parser.links:
        if is_ignored(link):
            continue
        if link.startswith("/"):
            broken.append(f"disallowed absolute link in {html_path}: {link}")
            continue
        target = strip_fragment(link)
        if not target:
            continue
        resolved = (html_path.parent / target).resolve()
        try:
            resolved.relative_to(site_root)
        except ValueError:
            broken.append(f"link escapes site root in {html_path}: {link}")
            continue
        if not resolved.exists():
            broken.append(f"missing target in {html_path}: {link}")

if broken:
    print("FAIL: local link check failed")
    for item in broken:
        print(f"- {item}")
    raise SystemExit(2)

print(f"PASS: local link check passed ({scanned} pages scanned)")
PY
