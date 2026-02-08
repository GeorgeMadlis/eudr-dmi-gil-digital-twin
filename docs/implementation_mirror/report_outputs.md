# AOI Report Outputs – Inspection Summary (Non-Authoritative)

## Purpose

This document describes AOI report artefacts for inspection and certification workflows.

## Source of Truth

- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/reports/README.md
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md

## Report Artefacts

- `report.html`
- `summary.json`
- supporting evidence artefacts (if applicable)

## AOI Forest Metrics & Evidence (Example Bundle)

The example bundle under docs/site/aoi_reports/runs/example/ is the reference for
inspection. The AOI report v2 exposes forest metrics and Hansen artefacts with
bundle-relative links in report.html.

Metric names used in v2 (forest metrics block and metrics.csv):

- rfm_area_ha
- loss_2021_2024_ha
- forest_end_year_area_ha

Method strings (forest metrics method block):

- geodesic_pixel_area_wgs84
- rasterize_polygon_all_touched

Evidence artefacts linked from report.html:

- forest_loss_post_2020_mask.geojson
- forest_current_tree_cover_mask.geojson
- forest_loss_post_2020_summary.json
- forest_loss_post_2020_tiles.json

## What Inspectors Should Be Able to Verify

- Offline navigation
- Bundle-relative links
- Alignment with policy-to-evidence spine acceptance criteria

## Public vs Private Handling

- Example runs may be published in the Digital Twin portal.
- Client reports are stored privately and are never committed to the DT repository.

## Testing & Validation Expectations

- Schema validation
- Hash consistency
- Deterministic regeneration

## How to Propose Output Changes

- Which artefact
- Which obligation (Art 9/10/11)
- Which acceptance criteria

## See also

- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/reports/README.md
- [DTE Instructions v1.1](../dte_instructions.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
