# Digital Twin View (EUDR DMI GIL)

Role in the ecosystem: This view is a public, non-authoritative Digital Twin portal artifact used for inspection and governance; authoritative implementation and deterministic outputs are produced in eudr-dmi-gil.

## Change loop: regulation × data × method
The EUDR Digital Twin is treated as an inspection-grade representation of:
- Authoritative regulation snapshots (mirrored, hashed, and versioned)
- Upstream datasets/services used as dependencies (with provenance)
- Project-owned methods + decision policies (deterministic, testable)
- Evidence bundles that link outcomes back to those sources

Primary model: [docs/architecture/digital_twin_model.md](../architecture/digital_twin_model.md)

## Trigger-and-rerun rules (high-level)
These rules describe what changes must force which re-runs.

### Regulation changes
If regulation source artifacts change fingerprint (SHA-256) or a new mirror run is recorded:
- Re-run all controls that cite those sources in provenance or acceptance criteria.
- Update/verify:
  - [docs/regulation/sources.json](../regulation/sources.json)
  - [docs/regulation/sources.md](../regulation/sources.md)

### Upstream dependency changes
If a dependency provenance/currency changes materially (new dataset version, endpoint behavior change, etc.):
- Re-run impacted methods and refresh provenance artifacts.
- Update the dependency register:
  - [docs/architecture/dependency_register.md](../architecture/dependency_register.md)

### Method / policy changes
If a project-owned method changes (logic, thresholds, canonicalization, output schema):
- Increment and record method versioning according to:
  - [docs/architecture/change_control.md](../architecture/change_control.md)
- Re-run impacted controls and refresh evidence bundles.

### Evidence schema / contract changes
If evidence bundle spec or contract changes:
- Update acceptance criteria mapping:
  - [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- Ensure operations guidance remains consistent:
  - [docs/operations/runbooks.md](../operations/runbooks.md)
  - [docs/operations/inspection_checklist.md](../operations/inspection_checklist.md)

## Canonical links
- Change control: [docs/architecture/change_control.md](../architecture/change_control.md)
- Evidence contract: [docs/architecture/evidence_contract.md](../architecture/evidence_contract.md)
- Policy-to-evidence spine: [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

## How stakeholders use this view in Q/A

- Review the change loop to frame questions about traceability and reproducibility.
- Validate which triggers should force re-runs before approving proposals.
- Capture stakeholder Q/A using the DAO stakeholder prompt: [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md).

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “digital-twin navigation view”
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22`

## See also

- [README.md](../../README.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
- [docs/agent_prompts/dao_dev_prompt.md](../agent_prompts/dao_dev_prompt.md)
