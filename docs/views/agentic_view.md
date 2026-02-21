# Agentic View (EUDR DMI GIL)

Role in the ecosystem: This view is a public, non-authoritative Digital Twin portal artifact used for inspection and governance; authoritative implementation and deterministic outputs are produced in eudr-dmi-gil.

## Agent roles
This view describes the intended agent/workflow split for producing inspection-grade artifacts.

- **Agent01 — Regulation mirror / watcher**
  - Owns deterministic acquisition/verification of regulation snapshots and their fingerprints.
  - Key docs: [docs/regulation/sources.md](../regulation/sources.md)
  - Tooling: https://github.com/single-earth/eudr-dmi-gil/blob/main/scripts/detect_example_bundle_artifact_changes.py

- **Agent02 — Evidence builder (article/control evaluation)**
  - Owns running project-owned method primitives and writing evidence artifacts.
  - Method primitives layer (owned here):
    - https://github.com/single-earth/eudr-dmi-gil/blob/main/src/eudr_dmi_gil/tasks/forest_loss_post_2020_clean.py
    - https://github.com/single-earth/eudr-dmi-gil/blob/main/src/eudr_dmi_gil/analysis/maaamet_validation.py
  - Article scaffolds:
    - https://github.com/single-earth/eudr-dmi-gil/blob/main/scripts/generate_report_v1.py

- **Agent03 — Inspector / verifier**
  - Owns verifying integrity/completeness/provenance against the contract and spine.
  - Key docs: [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md), https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/README.md

## Deterministic run contract (for all agents)
### Bundle root
Evidence bundles must be written under the evidence root, by date and bundle id:
- `<evidence_root>/<YYYY-MM-DD>/<bundle_id>/`

Filesystem roots are environment-driven:
- `EUDR_DMI_AUDIT_ROOT`, `EUDR_DMI_REGULATION_ROOT`, `EUDR_DMI_EVIDENCE_ROOT`
- See https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/operations/environment_setup.md

### Required inspection invariants
- Completeness + integrity rules are defined in:
  - https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/README.md
  - https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md
- Traceability rules are defined in:
  - [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

### What may contain timestamps
Determinism expectations are “byte-identical unless explicitly allowed”.
Allowed timestamp-bearing artifacts (example pattern):
- execution logs / run logs (must be excluded from equivalence checks or excluded from deterministic hashes)

See determinism rules in https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/README.md.

### Tests / sanity checks
- Method tests: `pytest -q -rs tests/test_methods_maa_amet_crosscheck.py`
- Report tests: https://github.com/single-earth/eudr-dmi-gil/blob/main/tests/test_reports_schema_validation.py

## Implementation inspection summaries

These mirrors are for inspection only. All changes must be proposed against authoritative files in eudr-dmi-gil.

- [docs/implementation_mirror/report_pipeline.md](../implementation_mirror/report_pipeline.md)
- [docs/implementation_mirror/dependency_model.md](../implementation_mirror/dependency_model.md)
- [docs/implementation_mirror/report_outputs.md](../implementation_mirror/report_outputs.md)

## How stakeholders use this view in Q/A

- Clarify which agent role is responsible for a reported issue or evidence gap.
- Use the role descriptions to scope questions before review.
- Capture stakeholder Q/A using the DAO stakeholder prompt: [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md).

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “agent-oriented navigation view”
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22`

## See also

- [README.md](../../README.md)
- DTE Instructions v1.3: [docs/dte_instructions.md](../dte_instructions.md)
- Inspection Index: [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
- [docs/agent_prompts/dao_dev_prompt.md](../agent_prompts/dao_dev_prompt.md)
