# Policy-to-Evidence Spine

## Purpose
This document provides the master mapping from obligations (e.g., regulatory articles) to control objectives and the concrete evidence artifacts that support inspection.

**Authority boundary:** This document provides inspectable mappings only. Authoritative logic, pipelines, and tests live in the implementation repository: https://github.com/georgemadlis/eudr-dmi-gil

## Boundary
This repo does not describe upstream platform internals (including `geospatial_dmi`). The “Produced By” column references agents/workflows and canonical entrypoints only.

Implementation references (authoritative):
- https://github.com/georgemadlis/eudr-dmi-gil/blob/main/docs/reports/README.md
- https://github.com/georgemadlis/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md

## Master Spine Table

| Obligation/Article | Control Objective | Evidence Artifact | Acceptance Criteria | Produced By (agent/workflow) | Evidence Path | Notes |
|---|---|---|---|---|---|---|
| Article 9 (Information requirements) | AOI geometry, operator-supplied inputs, and upstream dataset provenance are captured with enough detail to trace a published AOI result back to its source artefacts. | `inputs/aoi.geojson`<br />`bundle_manifest.json`<br />`reports/aoi_report_v2/<aoi_id>.json`<br />`report.html` | `bundle_manifest.json` lists the AOI JSON/HTML artefacts; `inputs/aoi.geojson` exists and matches the declared SHA-256; the AOI report JSON includes `aoi_geometry_ref`, `inputs.sources`, and `datasets`; report links in `report.html` resolve within the published run bundle. | `python -m eudr_dmi_gil.reports.cli` plus report analyses under `src/eudr_dmi_gil/analysis/` | `inputs/aoi.geojson`, `bundle_manifest.json`, `reports/aoi_report_v2/<aoi_id>.json`, `report.html` | Public inspection should follow the published run bundle contract, not legacy scaffold paths. The AOI report JSON is the declaration source of truth for evidence references. |
| Article 10 (Risk assessment) | Deforestation, forest-presence, and cross-check evidence for the AOI are computed and surfaced as inspectable results. | `reports/aoi_report_v2/<aoi_id>.json`<br />`reports/aoi_report_v2/<aoi_id>/hansen/forest_loss_post_2020_mask.geojson`<br />`reports/aoi_report_v2/<aoi_id>/hansen/forest_loss_post_2020_tiles.json`<br />`reports/aoi_report_v2/<aoi_id>/maaamet/maaamet_forest_area_crosscheck.json` (when present) | The AOI report JSON parses and includes `results_summary.deforestation_free_post_2020`, `forest_metrics`, and `policy_mapping`; linked Hansen artefacts resolve; when Maa-amet cross-check is enabled, the JSON cross-check summary is present and linked from the AOI report. | `python -m eudr_dmi_gil.reports.cli` orchestrating `forest_loss_post_2020.py`, `hansen_parcels.py`, and `maaamet_validation.py` | `reports/aoi_report_v2/<aoi_id>.json`, `reports/aoi_report_v2/<aoi_id>/hansen/forest_loss_post_2020_mask.geojson`, `reports/aoi_report_v2/<aoi_id>/hansen/forest_loss_post_2020_tiles.json`, `reports/aoi_report_v2/<aoi_id>/maaamet/maaamet_forest_area_crosscheck.json` | Evidence paths should match the generated AOI bundle layout used by the Digital Twin and client portal consumers. |
| Article 11 (Risk mitigation) | If the AOI result is not deforestation-free, the published artefacts must make the failure condition and follow-up evidence gaps inspectable. | `reports/aoi_report_v2/<aoi_id>.json`<br />`reports/aoi_report_v2/<aoi_id>.html` | The AOI report JSON includes failed `results[]`, `policy_mapping`, and thresholded `results_summary`; the HTML mirrors the status and links the supporting artefacts so an inspector can identify what needs review or mitigation. | `python -m eudr_dmi_gil.reports.cli` rendering the AOI JSON + HTML report pair | `reports/aoi_report_v2/<aoi_id>.json`, `reports/aoi_report_v2/<aoi_id>.html` | The current public contract exposes inspectable failure conditions; explicit mitigation-plan JSON is not yet part of the published AOI report bundle. |
| TODO_ARTICLE_REF_DEFINITIONS | Definition consistency / interpretability constraint (scaffold) | `definition_comparison.json` + `dependencies.json` | Artifacts present; parseable JSON; deterministic ordering; `outcome` defaults to `UNKNOWN` until extraction implemented; provenance hashes recorded for dependency run. | `scripts/task3/definition_comparison_control.py` | `method/definition_comparison.json`, `provenance/dependencies.json` | Scaffold for later NLP extraction and mismatch logic. |

### Update Notes (How to Maintain the Spine)
- Each new obligation/control MUST add a row and MUST reference a concrete artifact and acceptance criteria.
- Each evidence artifact MUST be aligned with the authoritative report contract in https://github.com/georgemadlis/eudr-dmi-gil/blob/main/docs/reports/README.md.
- Canonical implementation entrypoints referenced here should use the current `eudr_dmi_gil` namespace and the published AOI bundle contract.

## Inspector Checklist
- Each control objective has at least one artifact with objective acceptance criteria.
- Evidence paths are relative to the bundle root and resolve to real files.
- “Produced By” identifies the responsible workflow/agent version (recorded in manifest).

## How to propose changes

Use the DAO stakeholder prompt to submit questions or change proposals:
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)

## See also

- [README.md](../../README.md)
- [DTE Instructions v1.3](../dte_instructions.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/views/digital_twin_view.md](../views/digital_twin_view.md)
- https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/
