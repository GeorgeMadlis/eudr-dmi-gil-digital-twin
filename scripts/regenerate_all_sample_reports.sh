#!/usr/bin/env bash
# Regenerate all 4 sample reports from their source bundles
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

rm -rf docs/site/sample_reports/runs
mkdir -p docs/site/sample_reports

python3 "$SCRIPT_DIR/generate_sample_report_from_bundle.py" \
  --bundle-dir docs/site/bundles/runs/west_africa \
  --output-dir docs/site/sample_reports/Demo_Plot_01 \
  --report-json west_africa_aoi_report.json

python3 "$SCRIPT_DIR/generate_sample_report_from_bundle.py" \
  --bundle-dir docs/site/bundles/runs/se_asia \
  --output-dir docs/site/sample_reports/Demo_Plot_02 \
  --report-json se_asia_aoi_report.json

python3 "$SCRIPT_DIR/generate_sample_report_from_bundle.py" \
  --bundle-dir docs/site/bundles/runs/latin_america \
  --output-dir docs/site/sample_reports/Demo_Plot_03 \
  --report-json latin_america_aoi_report.json

python3 "$SCRIPT_DIR/generate_sample_report_from_bundle.py" \
  --bundle-dir docs/site/bundles/runs/example \
  --output-dir docs/site/sample_reports/Demo_Plot_04 \
  --report-json aoi_report.json

echo "All sample reports regenerated."
