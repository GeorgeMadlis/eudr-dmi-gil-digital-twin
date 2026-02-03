#!/usr/bin/env bash
set -euo pipefail

SITE_ROOT="docs/site"
RUNS_DIR="${SITE_ROOT}/aoi_reports/runs"
INDEX_FILE="${SITE_ROOT}/aoi_reports/index.html"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree is not clean. Commit or stash changes before cleaning." >&2
  git status --porcelain >&2
  exit 1
fi

if [[ -d "$RUNS_DIR" ]]; then
  echo "Deleting run directories under ${RUNS_DIR}/"
  while IFS= read -r -d '' entry; do
    echo "- ${entry}"
    rm -rf "${entry}"
  done < <(find "$RUNS_DIR" -mindepth 1 -maxdepth 1 -print0)
else
  echo "WARN: runs directory not found: ${RUNS_DIR}" >&2
fi

if [[ -f "$INDEX_FILE" ]]; then
  echo "Deleting ${INDEX_FILE}"
  rm -f "$INDEX_FILE"
else
  echo "WARN: index file not found: ${INDEX_FILE}" >&2
fi
