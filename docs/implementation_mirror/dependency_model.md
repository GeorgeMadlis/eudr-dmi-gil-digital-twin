# Dependency & Evidence Model – Inspection Summary (Non-Authoritative)

## Purpose

This document summarizes how dependencies and evidence sources are modeled for EUDR inspection and traceability.

## Source of Truth

- https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/architecture/dependency_register.md
- https://github.com/single-earth/eudr-dmi-gil/blob/main/docs/dependencies/sources.md

## What a Dependency Entry Represents

- ID
- External source (URL / provider)
- Content type
- Audit path / provenance
- “Used by” locations in code

## How Dependencies Appear in the Digital Twin

- Dependencies page
- Policy-to-evidence spine references

## Inspection Checklist

- Reproducibility
- Provenance clarity
- Explicit linkage to AOI outputs

## How to Propose Dependency Changes

- New source vs modification
- Required fields
- File-level grounding requirements

## See also

- [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
- [DTE Instructions v1.1](../dte_instructions.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
- [docs/agent_prompts/dao_dev_prompt.md](../agent_prompts/dao_dev_prompt.md)
