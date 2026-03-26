#!/usr/bin/env bash
set -euo pipefail

# Validate that only AOI report publish outputs are staged/modified.
# Allowed paths:
# - docs/site/aoi_reports/index.html
# - docs/site/aoi_reports/runs/

allowed_index="docs/site/aoi_reports/index.html"
allowed_runs_prefix="docs/site/aoi_reports/runs/"

changes="$(git status --porcelain)"
if [[ -z "$changes" ]]; then
  exit 0
fi

offenders=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # Strip status (first two columns) and space to get the path
  path="${line:3}"

  if [[ "$path" == "$allowed_index" ]]; then
    continue
  fi

  if [[ "$path" == "$allowed_runs_prefix"* ]]; then
    continue
  fi

  offenders+=("$path")
done <<< "$changes"

if (( ${#offenders[@]} > 0 )); then
  echo "ERROR: publish scope includes disallowed paths:" >&2
  for p in "${offenders[@]}"; do
    echo "  - $p" >&2
  done
  exit 1
fi

# Enforce deterministic AOI run set and resolvable index links.
runs_dir="docs/site/aoi_reports/runs"
if [[ ! -d "$runs_dir" ]]; then
  echo "ERROR: missing AOI runs directory: $runs_dir" >&2
  exit 1
fi

run_dirs=()
while IFS= read -r d; do
  [[ -z "$d" ]] && continue
  run_dirs+=("$d")
done < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d -print)
if (( ${#run_dirs[@]} != 4 )); then
  echo "ERROR: expected exactly four AOI run directories under $runs_dir" >&2
  for d in "${run_dirs[@]}"; do
    echo "  - $d" >&2
  done
  exit 1
fi

declare -A expected_json
expected_json[example]="estonia_aoi_report.json"
expected_json[latin_america]="latin_america_aoi_report.json"
expected_json[se_asia]="se_asia_aoi_report.json"
expected_json[west_africa]="west_africa_aoi_report.json"

index_path="docs/site/aoi_reports/index.html"

if [[ ! -f "$index_path" ]]; then
  echo "ERROR: missing AOI index: $index_path" >&2
  exit 1
fi

for run_id in example latin_america se_asia west_africa; do
  report_path="$runs_dir/$run_id/report.html"
  json_path="$runs_dir/$run_id/${expected_json[$run_id]}"

  if [[ ! -d "$runs_dir/$run_id" ]]; then
    echo "ERROR: missing required run directory: $runs_dir/$run_id" >&2
    exit 1
  fi

  if [[ ! -f "$report_path" ]]; then
    echo "ERROR: missing AOI report: $report_path" >&2
    exit 1
  fi

  if [[ ! -f "$json_path" ]]; then
    echo "ERROR: missing AOI JSON artefact: $json_path" >&2
    exit 1
  fi

  if ! grep -q "runs/$run_id/report.html" "$index_path"; then
    echo "ERROR: AOI index does not link to runs/$run_id/report.html" >&2
    exit 1
  fi
done

# Validate declared AOI artefacts exist and are linked from report.html.
python3 scripts/validate_aoi_run_artifacts.py --runs-dir "$runs_dir"
