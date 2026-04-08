#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from validate_aoi_run_artifacts import validate_run


ROOT_DIR = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT_DIR / "docs/site/bundles/runs/example"


def main() -> int:
    validate_run(RUN_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
