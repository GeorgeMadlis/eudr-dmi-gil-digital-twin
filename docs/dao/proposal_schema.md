# DAO Proposal Schema (YAML, File-Level Grounding)

## Design choice

- Use YAML
- One proposal = one file
- Store under: `dao/proposals/YYYY/MM/<slug>.yaml`

## DAO proposals output format (summary)

**Stakeholders**
- Questions raised
- Acceptance criteria decisions (pass/fail thresholds, evidence sufficiency)

**Developers**
- File-level changes
- Schema changes (if needed)
- Tests / validation
- Determinism guarantees
- Regeneration steps

## File-level grounding (enforced)

Every claim must be grounded to a DT URL or repo-relative path. If a claim cannot be grounded, mark it as `assumption` and list the missing evidence in `evidence_gaps`.

## Required fields (schema v1)

```yaml
schema_version: "1.0"
proposal_id: "SCP-YYYY-NNN-<slug>"
created_at: "YYYY-MM-DD"
status: "DRAFT"  # DRAFT | CONFIRMED | APPROVED | REJECTED | IMPLEMENTED
view: "dao_stakeholders"  # or dao_dev
stakeholder_confirmation: false

title: "<short title>"
summary: |
  <1-3 paragraphs explaining the change>

scope:
  affected_areas:
    - "reports"
    - "dependencies"
  affected_stage:
    - "evidence_acquisition"
    - "validation"

claims:
  - text: "<claim>"
    grounded_in:
      - "docs/regulation/policy_to_evidence_spine.md"
      - "https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/index.html"
    assumption: false

acceptance_criteria:
  - "<objective, testable criterion>"

evidence_refs:
  - path: "docs/regulation/policy_to_evidence_spine.md"
    reason: "<why this file matters>"

evidence_gaps:
  - "<missing artifact or URL>"

proposed_changes:
  - target_repo: "eudr-dmi-gil"
    target_path: "docs/architecture/decision_records/0001-report-pipeline-architecture.md"
    change_summary: "<what to change>"

review_notes: |
  <how a reviewer can verify using only the DT bundle>
```

## Notes

- Proposals must be confirmed by stakeholders before persistence (`stakeholder_confirmation: true`).
- All implementation changes must be proposed against authoritative files in eudr-dmi-gil.
