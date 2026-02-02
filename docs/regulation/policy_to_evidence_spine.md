# Policy-to-Evidence Spine

## Purpose
This document provides the master mapping from obligations (e.g., regulatory articles) to control objectives and the concrete evidence artifacts that support inspection.

**Authority boundary:** This document provides inspectable mappings only. Authoritative logic, pipelines, and tests live in the implementation repository: https://github.com/GeorgeMadlis/eudr-dmi-gil

## Boundary
This repo does not describe upstream platform internals (including `geospatial_dmi`). The “Produced By” column references agents/workflows and canonical entrypoints only.

Implementation references (authoritative):
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/reports/README.md
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md

## Master Spine Table

| Obligation/Article | Control Objective | Evidence Artifact | Acceptance Criteria | Produced By (agent/workflow) | Evidence Path | Notes |
|---|---|---|---|---|---|---|
| Article 9 (Information requirements) | AOI, inputs, and upstream dependencies are captured with provenance sufficient for traceability. | `inputs/geometry.*`<br />`inputs/parameters.json`<br />`provenance/provenance.json`<br />`manifest.json` + `hashes.sha256` | Inputs exist and are referenced by the manifest; JSON files parse; provenance entries are present for each used dependency and non-empty where required; recomputed SHA-256 matches `hashes.sha256` and the manifest (no missing artifacts). | `python -m eudr_dmi.articles.art_09.runner` (scaffold) | `inputs/geometry.*`, `inputs/parameters.json`, `provenance/provenance.json`, `manifest.json`, `hashes.sha256` | Current runner scaffolds write `manifest.sha256` + `bundle_metadata.json`; this row defines the target bundle contract used for inspection. |
| Article 10 (Risk assessment) | Deforestation and forest-presence signals are computed for the AOI and included in the assessment outcome. | `outputs/summary.json`<br />`outputs/deforestation.json` (or similar)<br />`outputs/maa_amet_crosscheck.json` | Outputs exist and are referenced by the manifest; JSON files parse; `outputs/summary.json` includes status and evidence references; deforestation + Maa-amet results include an explicit status and inputs fingerprint (or equivalent) so reruns are explainable; hashes verify (SHA-256 matches). | `python -m eudr_dmi.articles.art_10.runner` (scaffold) | `outputs/summary.json`, `outputs/deforestation.json` (or similar), `outputs/maa_amet_crosscheck.json` | Current runner scaffolds write `manifest.sha256`; outputs listed here are the intended stable contract for inspection once Step 3/4 land. |
| Article 11 (Risk mitigation) | If risk is not LOW, mitigation actions are stated and linked to evidence gaps or conflicts. | `outputs/mitigation_plan.json` | File exists and is referenced by the manifest; JSON parses; plan states the trigger condition (e.g., non-LOW/UNDETERMINED risk) and lists actions linked to specific evidence gaps/conflicts (artifact paths or decision ids); hashes verify (SHA-256 matches). | `python -m eudr_dmi.articles.art_11.runner` (scaffold) | `outputs/mitigation_plan.json` | This row defines the minimum mitigation-plan inspection contract; a deterministic scaffold can be emitted before full mitigation logic exists. |
| TODO_ARTICLE_REF_DEFINITIONS | Definition consistency / interpretability constraint (scaffold) | `definition_comparison.json` + `dependencies.json` | Artifacts present; parseable JSON; deterministic ordering; `outcome` defaults to `UNKNOWN` until extraction implemented; provenance hashes recorded for dependency run. | `scripts/task3/definition_comparison_control.py` | `method/definition_comparison.json`, `provenance/dependencies.json` | Scaffold for later NLP extraction and mismatch logic. |

### Update Notes (How to Maintain the Spine)
- Each new obligation/control MUST add a row and MUST reference a concrete artifact and acceptance criteria.
- Each evidence artifact MUST be defined in [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md).
- TODO: Add canonical references/links to any upstream entrypoints used (without describing upstream architecture).

## Inspector Checklist
- Each control objective has at least one artifact with objective acceptance criteria.
- Evidence paths are relative to the bundle root and resolve to real files.
- “Produced By” identifies the responsible workflow/agent version (recorded in manifest).

## How to propose changes

Use the DAO stakeholder prompt to submit questions or change proposals:
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)

## See also

- [README.md](../../README.md)
- [docs/governance/dte_instructions.md](../governance/dte_instructions.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/views/digital_twin_view.md](../views/digital_twin_view.md)
- https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/
