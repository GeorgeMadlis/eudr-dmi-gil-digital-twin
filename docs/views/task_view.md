# Task View (EUDR DMI GIL)

Role in the ecosystem: This view is a public, non-authoritative Digital Twin portal artifact used for inspection and governance; authoritative implementation and deterministic outputs are produced in eudr-dmi-gil.

## Task framing
This view organizes the repo by the operator/inspection tasks it must support.

- **Task 1 — Establish authoritative inputs**: ensure regulation snapshots and upstream dependencies are recorded, traceable, and verifiable.
- **Task 2 — Produce method outcomes**: run deterministic EUDR methods (or scaffolds) and record outputs with stable fingerprints.
- **Task 3 — Package for inspection**: produce evidence bundles with integrity metadata and clear acceptance criteria.

## Task-to-artifact map

| Task | What “done” means | Canonical artifacts (paths) | Tests / checks |
|---|---|---|---|
| Task 1: authoritative inputs | Regulation sources are referenced and can be verified without embedding regulation text in-repo. | [docs/regulation/sources.md](../regulation/sources.md), [docs/regulation/links.html](../regulation/links.html), https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/dependencies/sources.md, https://github.com/single-earth/eudr-dmi-gil/blob/main/scripts/validate_dependency_links.py | `python3 scripts/validate_dao_reports_links.py` (DT), plus https://github.com/single-earth/eudr-dmi-gil/blob/main/tests/test_validate_dependency_links_offline.py |
| Task 2: method outcomes | Deterministic report and analysis outputs have stable fingerprints and reproducible generation steps. | https://github.com/single-earth/eudr-dmi-gil/blob/main/src/eudr_dmi_gil/tasks/forest_loss_post_2020_clean.py, https://github.com/single-earth/eudr-dmi-gil/blob/main/src/eudr_dmi_gil/analysis/maaamet_validation.py, https://github.com/single-earth/eudr-dmi-gil/blob/main/scripts/generate_report_v1.py, https://github.com/single-earth/eudr-dmi-gil/blob/main/scripts/check_method_deps.py | `python scripts/check_method_deps.py`, `pytest -q -rs tests/test_methods_maa_amet_crosscheck.py` |
| Task 3: inspection packaging | Report contracts and runbooks define what to produce and how to verify before publish. | https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/README.md, https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md, [docs/implementation_mirror/report_outputs.md](../implementation_mirror/report_outputs.md), https://github.com/single-earth/eudr-dmi-gil/blob/main/tools/publish_latest_aoi_reports_to_dt.py | `python3 scripts/validate_aoi_run_artifacts.py`, `python3 scripts/test_aoi_report_integration.py` |

## How stakeholders use this view in Q/A

- Identify which inspection task is impacted by a question or evidence gap.
- Use the task-to-artifact map to locate the relevant public artefacts for review.
- Capture stakeholder Q/A using the DAO stakeholder prompt: [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md).

## Key navigation shortcuts
- Inspection index (authoritative): https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/INSPECTION_INDEX.md
- Report runbook (authoritative): https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/reports/runbook_generate_aoi_report.md
- Policy-to-evidence spine: [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- Environment setup: https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/operations/environment_setup.md
- Report CLI: https://github.com/single-earth/eudr-dmi-gil/blob/main/src/eudr_dmi_gil/reports/cli.py

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “task-oriented navigation view”
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
