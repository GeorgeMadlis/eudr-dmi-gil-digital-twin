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
- [docs/governance/dte_instructions.md](../governance/dte_instructions.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)
