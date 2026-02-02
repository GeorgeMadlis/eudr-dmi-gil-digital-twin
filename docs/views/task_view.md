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
| Task 1: authoritative inputs | Regulation sources are referenced and can be verified without embedding regulation text in-repo. | [docs/regulation/sources.md](../regulation/sources.md), [docs/regulation/sources.json](../regulation/sources.json), [docs/regulation/links.html](../regulation/links.html), [tools/regulation/acquire_and_hash.py](../../tools/regulation/acquire_and_hash.py) | `python tools/regulation/acquire_and_hash.py --verify` (server files), plus [tests/test_regulation_registry_files_exist.py](../../tests/test_regulation_registry_files_exist.py) |
| Task 2: method outcomes | Deterministic method primitives exist and have stable input fingerprints; expected skips are documented. | [src/eudr_dmi/methods/deforestation_area.py](../../src/eudr_dmi/methods/deforestation_area.py), [src/eudr_dmi/methods/maa_amet_crosscheck.py](../../src/eudr_dmi/methods/maa_amet_crosscheck.py), [requirements-methods.txt](../../requirements-methods.txt), [scripts/check_method_deps.py](../../scripts/check_method_deps.py), [docs/testing.md](../testing.md) | `python scripts/check_method_deps.py`, `pytest -q -rs tests/test_methods_*` (see [tests/test_methods_deforestation_area.py](../../tests/test_methods_deforestation_area.py), [tests/test_methods_maa_amet_crosscheck.py](../../tests/test_methods_maa_amet_crosscheck.py)) |
| Task 3: inspection packaging | Evidence contracts and checklists define what to produce and how to verify; PRs are gated on canonical doc structure. | [docs/architecture/evidence_contract.md](../architecture/evidence_contract.md), [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md), [docs/operations/inspection_checklist.md](../operations/inspection_checklist.md), [tools/ci/check_pr_gates.py](../../tools/ci/check_pr_gates.py) | `python tools/ci/check_pr_gates.py` (CI gate), plus [tests/articles/test_articles_structure_smoke.py](../../tests/articles/test_articles_structure_smoke.py) |

## How stakeholders use this view in Q/A

- Identify which inspection task is impacted by a question or evidence gap.
- Use the task-to-artifact map to locate the relevant public artefacts for review.
- Capture stakeholder Q/A using the DAO stakeholder prompt: [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md).

## Key navigation shortcuts
- Evidence contract: [docs/architecture/evidence_contract.md](../architecture/evidence_contract.md)
- Evidence bundle spec: [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md)
- Policy-to-evidence spine: [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- Runbook: [docs/operations/runbooks.md](../operations/runbooks.md)
- Article 09 scaffold runner: [src/eudr_dmi/articles/art_09/runner.py](../../src/eudr_dmi/articles/art_09/runner.py)

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “task-oriented navigation view”
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22`

## See also

- [README.md](../../README.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
- [docs/agent_prompts/dao_dev_prompt.md](../agent_prompts/dao_dev_prompt.md)
