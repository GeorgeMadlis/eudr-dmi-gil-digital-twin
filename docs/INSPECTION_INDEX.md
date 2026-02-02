# Inspection Index (Authoritative Implementation)

This index enumerates all authoritative documentation relevant for
EUDR DAO inspection, proposal formulation, and developer implementation
in the eudr-dmi-gil repository.

It is the canonical entry point for:
- Stakeholders inspecting implementation behaviour via the Digital Twin
- AI engines (EUDR DAO Digital Twin Engineer or similar)
- Developers reviewing or implementing DAO proposals

## Authority boundary

- This repository (**eudr-dmi-gil**) is the authoritative source for:
  - Evidence contracts
  - Data acquisition and validation logic
  - AOI report generation pipelines
  - Deterministic outputs and tests
- The Digital Twin repository is the public, non-authoritative inspection
  and governance portal:
  https://github.com/GeorgeMadlis/eudr-dmi-gil-digital-twin

Inspection, critique, and proposals may reference this repository,
but no compliance claims are made here.

## Mandatory grounding rule

Any DAO proposal that recommends changes to implementation MUST:
- Reference one or more files listed in this index (path-level grounding), or
- Explicitly state an evidence gap if grounding is not possible.

## Architecture

- Report pipeline architecture (ADR)  
  → docs/architecture/decision_records/0001-report-pipeline-architecture.md
- Dependency register (logical model)  
  → docs/architecture/dependency_register.md

## Dependencies and Evidence Sources

- Dependency model overview  
  → docs/dependencies/README.md
- Evidence source definitions (authoritative)  
  → docs/dependencies/sources.md

## Reports and Outputs

- Report structure, guarantees, and artefacts  
  → docs/reports/README.md
- AOI report generation runbook  
  → docs/reports/runbook_generate_aoi_report.md

## Operations (Execution Environment)

- Environment setup  
  → docs/operations/environment_setup.md
- MinIO configuration (private artefact storage)  
  → docs/operations/minio_setup.md
- Migration and regeneration procedures  
  → docs/operations/migration_runbook.md

## Related inspection surface (Digital Twin)

For public inspection, examples, and DAO workflows, see:
- Digital Twin portal (GitHub Pages):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/index.html
- Digital Twin repository:
  https://github.com/GeorgeMadlis/eudr-dmi-gil-digital-twin
