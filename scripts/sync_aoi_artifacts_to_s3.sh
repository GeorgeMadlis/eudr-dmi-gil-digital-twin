#!/usr/bin/env bash
set -euo pipefail

# Sync AOI run artifacts to S3-compatible object storage.
#
# Required env vars:
#   S3_ARTIFACTS_URI   e.g. s3://my-bucket/eudr/digital-twin/aoi-reports
#
# Optional env vars:
#   S3_ENDPOINT_URL    e.g. https://s3.pilw.io
#   SOURCE_DIR         default: docs/site/aoi_reports/runs
#   DRY_RUN            default: false
#   DELETE_EXTRA       default: false
#   S3_FORCE_PATH_STYLE default: true

S3_ARTIFACTS_URI="${S3_ARTIFACTS_URI:-}"
S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-}"
SOURCE_DIR="${SOURCE_DIR:-docs/site/aoi_reports/runs}"
DRY_RUN="${DRY_RUN:-false}"
DELETE_EXTRA="${DELETE_EXTRA:-false}"
S3_FORCE_PATH_STYLE="${S3_FORCE_PATH_STYLE:-true}"

if [[ -z "${S3_ARTIFACTS_URI}" ]]; then
  echo "ERROR: S3_ARTIFACTS_URI is required" >&2
  exit 2
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "ERROR: SOURCE_DIR does not exist: ${SOURCE_DIR}" >&2
  exit 2
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: aws CLI is required but not found in PATH" >&2
  exit 2
fi

if [[ "${S3_FORCE_PATH_STYLE}" == "true" ]]; then
  export AWS_S3_ADDRESSING_STYLE=path
fi

aws_cli=(aws)
if [[ -n "${S3_ENDPOINT_URL}" ]]; then
  aws_cli+=(--endpoint-url "${S3_ENDPOINT_URL}")
fi

sync_args=(s3 sync "${SOURCE_DIR}/" "${S3_ARTIFACTS_URI%/}/" --only-show-errors)

if [[ "${DELETE_EXTRA}" == "true" ]]; then
  sync_args+=(--delete)
fi

if [[ "${DRY_RUN}" == "true" ]]; then
  sync_args+=(--dryrun)
fi

echo "Syncing AOI artifacts to ${S3_ARTIFACTS_URI%/}/"
echo "  source: ${SOURCE_DIR}"
echo "  dry_run: ${DRY_RUN}"
echo "  delete_extra: ${DELETE_EXTRA}"
if [[ -n "${S3_ENDPOINT_URL}" ]]; then
  echo "  endpoint: ${S3_ENDPOINT_URL}"
fi
echo "  force_path_style: ${S3_FORCE_PATH_STYLE}"
"${aws_cli[@]}" "${sync_args[@]}"

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "Dry-run mode enabled, skipping sync manifest upload."
  exit 0
fi

git_commit="$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
generated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
tmp_manifest="$(mktemp)"

cat > "${tmp_manifest}" <<EOF
{
  "generated_at_utc": "${generated_at}",
  "git_commit": "${git_commit}",
  "source_dir": "${SOURCE_DIR}",
  "s3_uri": "${S3_ARTIFACTS_URI%/}/",
  "s3_endpoint_url": "${S3_ENDPOINT_URL}"
}
EOF

"${aws_cli[@]}" s3 cp "${tmp_manifest}" "${S3_ARTIFACTS_URI%/}/_sync_manifest.json" --only-show-errors
rm -f "${tmp_manifest}"

echo "Sync complete."
