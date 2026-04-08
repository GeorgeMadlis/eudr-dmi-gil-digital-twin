#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def assert_contains(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"Missing expected link in {path}: {needle}")


def main() -> int:
    p = argparse.ArgumentParser(description="Check AOI nav links for correct rel_prefix.")
    p.add_argument("--site-root", default="docs/site", help="Root folder containing site HTML")
    p.add_argument("--run-id", required=True, help="AOI run id to check")
    args = p.parse_args()

    site_root = Path(args.site_root)

    assert_contains(site_root / "bundles" / "index.html", 'href="../articles/index.html"')
    assert_contains(site_root / "bundles" / "index.html", 'href="../dependencies/index.html"')
    assert_contains(site_root / "bundles" / "index.html", 'href="../regulation/links.html"')
    assert_contains(site_root / "bundles" / "index.html", 'href="../regulation/policy_to_evidence_spine.html"')
    assert_contains(site_root / "bundles" / "index.html", 'href="../dao_dev/index.html"')

    run_path = site_root / "bundles" / "runs" / args.run_id / "report.html"
    assert_contains(run_path, 'href="../../../index.html"')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
