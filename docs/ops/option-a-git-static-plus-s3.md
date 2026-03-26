# Setup: Git-Hosted Static Site + S3-Compatible (Ceph) Artifact Mirror

This setup keeps static portal pages in Git-hosted publishing and mirrors AOI run artifacts to S3-compatible object storage.

## Scope

- Static content source: `docs/site/**`
- Artifact sync source: `docs/site/aoi_reports/runs/**`
- Sync script: `scripts/sync_aoi_artifacts_to_s3.sh`
- CI workflow: `.github/workflows/validate-and-sync-artifacts.yml`

## 1. GitHub repository configuration

Set these repository variables/secrets:

Required:
- `S3_ARTIFACTS_URI` (Repository variable), example: `s3://my-bucket/eudr/digital-twin/aoi-reports`
- `S3_ENDPOINT_URL` (Repository variable), example: `https://s3.pilw.io`

For Ceph / `s3.pilw.io`:
- `S3_FORCE_PATH_STYLE` (Repository variable), recommended: `true`
- `S3_REGION` (Repository variable), optional, default fallback in workflow: `us-east-1`

Required secrets:
- `S3_ACCESS_KEY_ID` (Repository secret)
- `S3_SECRET_ACCESS_KEY` (Repository secret)

## 2. IAM minimum permissions

The CI principal should have least-privilege access for:
- `s3:ListBucket` on the target bucket
- `s3:PutObject` on the target prefix
- `s3:GetObject` on the target prefix
- `s3:DeleteObject` only if `DELETE_EXTRA=true` is used

## 3. Workflow behavior

The workflow validates artifacts first:
- `python3 scripts/validate_aoi_run_artifacts.py --runs-dir docs/site/aoi_reports/runs`
- `python3 scripts/test_aoi_report_renderer.py`
- `python3 scripts/test_aoi_report_integration.py`
- `scripts/check_links_local.sh --site-root docs/site`
- `python3 scripts/check_nav_links.py --site-root docs/site --run-id example`

After validation, S3 sync runs only when `S3_ARTIFACTS_URI` is configured.
If `S3_ENDPOINT_URL` is set (for example `https://s3.pilw.io`), sync is executed against that endpoint.

## 4. Manual dry-run from local machine

```bash
cd eudr-dmi-gil-digital-twin
export S3_ARTIFACTS_URI="s3://my-bucket/eudr/digital-twin/aoi-reports"
export S3_ENDPOINT_URL="https://s3.pilw.io"
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export DRY_RUN=true
scripts/sync_aoi_artifacts_to_s3.sh
```

## 5. Safety notes

- Keep `DELETE_EXTRA=false` by default to avoid accidental object removal.
- Do not store credentials in repository files.
- For Ceph S3 endpoints, keep `S3_FORCE_PATH_STYLE=true` unless your endpoint supports virtual-host style bucket addressing.
