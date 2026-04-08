#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from site_nav import render_header_nav  # noqa: E402


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
CODE_RE = re.compile(r"`([^`]+)`")


def format_inline(text: str) -> str:
  text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
  text = BOLD_RE.sub(r"<strong>\1</strong>", text)
  text = CODE_RE.sub(r"<code>\1</code>", text)
  return text


def render_markdown(md_text: str) -> str:
  lines = md_text.splitlines()
  out: list[str] = []
  in_code = False
  list_stack: list[str] = []

  def close_lists() -> None:
    while list_stack:
      out.append(f"</{list_stack.pop()}>")

  for raw in lines:
    line = raw.rstrip()

    if line.startswith("```"):
      if in_code:
        out.append("</code></pre>")
        in_code = False
      else:
        close_lists()
        out.append("<pre><code>")
        in_code = True
      continue

    if in_code:
      out.append(html.escape(line))
      continue

    if not line.strip():
      close_lists()
      continue

    if line.startswith("# "):
      close_lists()
      out.append(f"<h1>{format_inline(line[2:])}</h1>")
      continue
    if line.startswith("## "):
      close_lists()
      out.append(f"<h2>{format_inline(line[3:])}</h2>")
      continue
    if line.startswith("### "):
      close_lists()
      out.append(f"<h3>{format_inline(line[4:])}</h3>")
      continue

    if line.startswith("> "):
      close_lists()
      out.append(f"<blockquote>{format_inline(line[2:])}</blockquote>")
      continue

    if line.lstrip().startswith("<"):
      close_lists()
      out.append(line)
      continue

    ordered_match = re.match(r"^(\d+)\.\s+(.*)$", line)
    if ordered_match:
      if not list_stack or list_stack[-1] != "ol":
        close_lists()
        list_stack.append("ol")
        out.append("<ol>")
      out.append(f"<li>{format_inline(ordered_match.group(2))}</li>")
      continue

    if line.startswith("- "):
      if not list_stack or list_stack[-1] != "ul":
        close_lists()
        list_stack.append("ul")
        out.append("<ul>")
      out.append(f"<li>{format_inline(line[2:])}</li>")
      continue

    close_lists()
    out.append(f"<p>{format_inline(line)}</p>")

  if in_code:
    out.append("</code></pre>")

  close_lists()
  return "\n".join(out)


def build_page(*, body_html: str) -> str:
    header_html = render_header_nav(rel_prefix="", active_label="DTE Instructions v1.4")
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>DTE Instructions v1.4</title>
    <style>
      :root {{ --fg:#111; --bg:#fff; --muted:#666; --card:#f6f7f9; --link:#0b5fff; }}
      body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
             color: var(--fg); background: var(--bg); margin: 0; }}
      header {{ border-bottom: 1px solid #e7e7e7; background: #fff; position: sticky; top: 0; }}
      .wrap {{ max-width: 980px; margin: 0 auto; padding: 16px 20px; }}
      nav a {{ margin-right: 14px; text-decoration: none; color: var(--link); font-weight: 600; }}
      nav a.active {{ color: var(--fg); }}
      .crumbs {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
      .crumbs a {{ color: var(--link); text-decoration: none; font-weight: 600; }}
      .crumbs .sep {{ margin: 0 6px; color: #999; }}
      main {{ padding: 18px 20px 40px; }}
      h1 {{ margin: 0 0 6px; font-size: 22px; }}
      h2 {{ margin-top: 24px; font-size: 18px; }}
      p {{ line-height: 1.5; }}
      .muted {{ color: var(--muted); }}
      .back {{ margin: 0 0 10px; }}
      .back a {{ color: var(--link); text-decoration: none; font-weight: 600; }}
      .card {{ background: var(--card); border: 1px solid #e8eaee; border-radius: 12px; padding: 14px 14px; }}
      ul {{ padding-left: 18px; }}
      code {{ background: #f1f1f1; padding: 1px 4px; border-radius: 6px; }}
      .md {{ line-height: 1.55; }}
      .md table {{ border-collapse: collapse; }}
      .md th, .md td {{ border: 1px solid #dde0e6; padding: 6px 10px; }}
      .md thead th {{ background: #eef1f6; }}
      .md .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
      .md .table-wrap table {{ width: max-content; min-width: 100%; }}
      .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; }}
      @media (min-width: 760px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
    </style>
  </head>
  <body>
    {header_html}
    <main>
      <div class=\"wrap\">
        <div class=\"md\">
{body_html}
        </div>
      </div>
    </main>
    <footer style=\"border-top:1px solid #e7e7e7; background:#fff;\">
      <div style=\"max-width:980px; margin:0 auto; padding:18px 20px 28px; color:#666; font-size:13px;\">
        <a href=\"privacy.html\" style=\"color:#0b5fff; text-decoration:none; font-weight:600;\">Privacy Policy</a>
      </div>
    </footer>
  </body>
</html>
"""


def render_to_site(*, source_path: Path, site_root: Path) -> None:
  if not source_path.is_file():
    raise SystemExit(f"Source markdown not found: {source_path}")

  site_root.mkdir(parents=True, exist_ok=True)
  body_html = render_markdown(source_path.read_text(encoding="utf-8"))
  output_path = site_root / "dte_instructions.html"
  output_path.write_text(build_page(body_html=body_html), encoding="utf-8")


def main() -> int:
  p = argparse.ArgumentParser(description="Render DTE instructions to site HTML.")
  p.add_argument("--source", default="docs/dte_instructions.md", help="Source markdown file")
  p.add_argument("--site-root", default="docs/site", help="Site root for output HTML")
  args = p.parse_args()

  render_to_site(source_path=Path(args.source), site_root=Path(args.site_root))
  return 0


if __name__ == "__main__":
    raise SystemExit(main())
