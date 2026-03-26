# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Four-Repo Project Overview

This repo is one of four that form the EUDR evidence platform, all under the `georgemadlis` GitHub account:

| Repo | Role |
|------|------|
| **eudr-dmi-gil-digital-twin** ← (this repo) | Public Digital Twin — inspectable example outputs, DAO governance, GitHub Pages site |
| **eudr-dmi-gil** | Authoritative generation — publishes `out/site_bundle/` here via scripts |
| **eudr-client-portal** | Private web portal — links to this site for demo reports |
| **eudr-dmi-gil-digital-twin-ai-mirror** | CI-maintained mirror of `docs/site/` for AI inspection |

This repo is **non-authoritative**. It contains only example outputs and governance templates. All authoritative report generation happens in `eudr-dmi-gil`.

---

## Public Site

**GitHub Pages URL:** `https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/`

The site root is `docs/site/`. GitHub Pages serves this directory directly (`.nojekyll` disables Jekyll). The URL must be accessed via GitHub Pages — raw file URLs on `github.com` are not the website.

---

## Commands

```bash
# Validate artifact integrity
python3 scripts/validate_aoi_run_artifacts.py

# Validate DAO report links
python3 scripts/validate_dao_reports_links.py

# Test AOI report rendering
python3 scripts/test_aoi_report_renderer.py
python3 scripts/test_aoi_report_integration.py

# Verify local links (for GitHub Pages + file://)
bash scripts/check_links_local.sh --site-root docs/site

# Clean all AOI runs before receiving a new publish bundle
bash scripts/clean_aoi_reports.sh

# Sync AOI artifacts to S3 (optional, for scale)
bash scripts/sync_aoi_artifacts_to_s3.sh
```

---

## Site Structure

```
docs/
└── site/                            # GitHub Pages root
    ├── index.html                   # Portal home
    ├── aoi_reports/
    │   ├── index.html               # Auto-generated run index
    │   └── runs/
    │       └── <run_id>/
    │           ├── report.html
    │           ├── aoi_report.json  # Source of truth for declared artifacts
    │           └── reports/aoi_report_v2/<plot>.json
    ├── dao_reports/runs/            # DAO inspection reports
    ├── dao_dev/proposals/           # Developer DAO interface
    ├── dao_stakeholders/proposals/  # Stakeholder DAO interface
    ├── regulation/                  # Policy-to-evidence spine
    ├── views/                       # DT views
    ├── dependencies/                # Dependency artifacts
    └── articles/                    # Educational content
```

**Canonical docs (read these before making governance changes):**
- `docs/dte_instructions.md` — DTE role, Q&A rules, proposal closeout
- `docs/INSPECTION_INDEX.md` — index of all inspectable artifacts
- `docs/dao/dao_proposal_schema.yaml` — YAML schema for proposals

---

## Receiving a Publish Bundle from eudr-dmi-gil

The `eudr-dmi-gil` repo publishes here via `scripts/publish_aoi_reports_to_dt.sh` or `tools/publish_latest_aoi_reports_to_dt.py`. That script:

1. Runs `bash scripts/clean_aoi_reports.sh` (clears existing runs — mandatory)
2. Copies the new run bundle into `docs/site/aoi_reports/runs/`
3. Regenerates `docs/site/aoi_reports/index.html`
4. Runs link validation
5. Commits and pushes — GitHub Pages redeploys automatically

**Artifact publication contract:**
- `aoi_report.json` is the source of truth for what artifacts must exist
- `report.html` must link to all declared artifacts
- Build (CI) fails if any artifact is missing or unlinked
- **Delete-before-publish invariant:** always clean before copying new bundle to prevent stale artifacts

---

## AI Mirror (CI)

`.github/workflows/publish-ai-mirror.yml` runs on every push to `main`:
1. Renders DTE instructions and rebuilds the AOI reports index
2. Validates links
3. Force-pushes the entire `docs/site/` to `georgemadlis/eudr-dmi-gil-digital-twin-ai-mirror`

Required secret: `AI_MIRROR_PUSH_TOKEN` — a PAT with write access to the ai-mirror repo.

---

## DAO Governance

The DAO here is **procedural** (not blockchain). It uses Git versioning + human-in-the-loop review as its governance mechanism.

**Proposal lifecycle:**
1. Stakeholder submits question/proposal via portal templates in `docs/agent_prompts/`
2. DTE (AI inspection engine) reviews and generates a proposal following `docs/dte_instructions.md`
3. Developer reviews proposal, implements in `eudr-dmi-gil`
4. Pipelines regenerate evidence, publish updated bundle here

All proposals must be grounded in URLs from this site or indexed repo paths — no unverified claims.
