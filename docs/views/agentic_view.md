# Agentic View (EUDR DMI GIL)

Role in the ecosystem: This view is a public, non-authoritative Digital Twin portal artifact used for inspection and governance; authoritative implementation and deterministic outputs are produced in eudr-dmi-gil.

## Agent roles
This view describes the intended agent/workflow split for producing inspection-grade artifacts.

- **Agent01 — Regulation mirror / watcher**
  - Owns deterministic acquisition/verification of regulation snapshots and their fingerprints.
  - Key docs: [docs/regulation/sources.md](../regulation/sources.md)
  - Tooling: [tools/regulation/acquire_and_hash.py](../../tools/regulation/acquire_and_hash.py)

- **Agent02 — Evidence builder (article/control evaluation)**
  - Owns running project-owned method primitives and writing evidence artifacts.
  - Method primitives layer (owned here):
    - [src/eudr_dmi/methods/deforestation_area.py](../../src/eudr_dmi/methods/deforestation_area.py)
    - [src/eudr_dmi/methods/maa_amet_crosscheck.py](../../src/eudr_dmi/methods/maa_amet_crosscheck.py)
  - Article scaffolds:
    - [src/eudr_dmi/articles/art_09/runner.py](../../src/eudr_dmi/articles/art_09/runner.py)

- **Agent03 — Inspector / verifier**
  - Owns verifying integrity/completeness/provenance against the contract and spine.
  - Key docs: [docs/operations/inspection_checklist.md](../operations/inspection_checklist.md), [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

## Deterministic run contract (for all agents)
### Bundle root
Evidence bundles must be written under the evidence root, by date and bundle id:
- `<evidence_root>/<YYYY-MM-DD>/<bundle_id>/`

Filesystem roots are environment-driven:
- `EUDR_DMI_AUDIT_ROOT`, `EUDR_DMI_REGULATION_ROOT`, `EUDR_DMI_EVIDENCE_ROOT`
- See [docs/operations/runbooks.md](../operations/runbooks.md)

### Required inspection invariants
- Completeness + integrity rules are defined in:
  - [docs/architecture/evidence_contract.md](../architecture/evidence_contract.md)
  - [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md)
- Traceability rules are defined in:
  - [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

### What may contain timestamps
Determinism expectations are “byte-identical unless explicitly allowed”.
Allowed timestamp-bearing artifacts (example pattern):
- execution logs / run logs (must be excluded from equivalence checks or excluded from deterministic hashes)

See determinism rules in [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md).

### Tests / sanity checks
- Method tests: `pytest -q -rs tests/test_methods_*` (see [docs/testing.md](../testing.md))
- Doc structure checks: [tests/articles/test_articles_structure_smoke.py](../../tests/articles/test_articles_structure_smoke.py)

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
- DTE Instructions v1.1: [docs/dte_instructions.md](../dte_instructions.md)
- Inspection Index: [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
- [docs/agent_prompts/dao_dev_prompt.md](../agent_prompts/dao_dev_prompt.md)
