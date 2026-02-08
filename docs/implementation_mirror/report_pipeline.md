# Report Pipeline – Inspection Summary (Non-Authoritative)

## Purpose

This document summarizes the AOI report generation pipeline for inspection and DAO governance. It is **NON-authoritative**.

## Source of Truth

Authoritative ADR:
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/architecture/decision_records/0001-report-pipeline-architecture.md

Implementation changes must be proposed against that file.

## High-Level Pipeline Overview

- AOI definition
- Evidence acquisition
- Evidence validation
- Metric computation
- Report materialization (HTML + JSON)
- Export to Digital Twin (examples only)

## AOI Forest Metrics (Inspection Notes)

The example AOI report bundle in docs/site/aoi_reports/runs/example/ reflects the current
authoritative implementation outputs. Inspectors should expect:

- Metric names used in v2 reports:
	- rfm_area_ha
	- loss_2021_2024_ha
	- forest_end_year_area_ha
- Method strings in the forest metrics block:
	- area: geodesic_pixel_area_wgs84
	- zonal: rasterize_polygon_all_touched
- Hansen artifacts listed in the run-level report.html with bundle-relative links:
	- forest_loss_post_2020_mask.geojson
	- forest_current_tree_cover_mask.geojson
	- forest_loss_post_2020_summary.json
	- forest_loss_post_2020_tiles.json

## Determinism Guarantees (Inspection-Relevant)

- Stable ordering
- No timestamps in outputs
- Hash-addressed artefacts
- Re-runnable regeneration

## Public vs Private Outputs

- Example reports may be exported to the Digital Twin portal for public inspection.
- Client AOI reports are stored privately and are never committed to the DT repository.

## How Stakeholders Should Propose Changes

- Reference authoritative file paths in eudr-dmi-gil.
- Specify which pipeline stage is affected.
- Include acceptance criteria.

## See also

- [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
- [DTE Instructions v1.1](../dte_instructions.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
