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

# Enforce single stable AOI example run and resolvable index link.
runs_dir="docs/site/aoi_reports/runs"
if [[ ! -d "$runs_dir" ]]; then
  echo "ERROR: missing AOI runs directory: $runs_dir" >&2
  exit 1
fi

mapfile -t run_dirs < <(find "$runs_dir" -mindepth 1 -maxdepth 1 -type d -print)
if (( ${#run_dirs[@]} != 1 )); then
  echo "ERROR: expected exactly one AOI run directory under $runs_dir" >&2
  for d in "${run_dirs[@]}"; do
    echo "  - $d" >&2
  done
  exit 1
fi

run_name="$(basename "${run_dirs[0]}")"
if [[ "$run_name" != "example" ]]; then
  echo "ERROR: expected only the 'example' run directory, found: $run_name" >&2
  exit 1
fi

report_path="$runs_dir/example/report.html"
json_path="$runs_dir/example/aoi_report.json"
index_path="docs/site/aoi_reports/index.html"

if [[ ! -f "$report_path" ]]; then
  echo "ERROR: missing AOI report: $report_path" >&2
  exit 1
fi

if [[ ! -f "$json_path" ]]; then
  echo "ERROR: missing AOI JSON artefact: $json_path" >&2
  exit 1
fi

if [[ ! -f "$index_path" ]]; then
  echo "ERROR: missing AOI index: $index_path" >&2
  exit 1
fi

if ! grep -q "runs/example/report.html" "$index_path"; then
  echo "ERROR: AOI index does not link to runs/example/report.html" >&2
  exit 1
fi
