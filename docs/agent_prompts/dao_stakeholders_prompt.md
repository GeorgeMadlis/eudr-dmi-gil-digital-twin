# DAO (Stakeholders) — Agent Prompt

## Start Here

1) If the bundle contains `machine/bundle_manifest.yaml`, start there.
2) Otherwise start at `machine/dao_stakeholders/view.yaml`.

## Canonical DTE Instructions

These prompts are governed by the canonical DTE instructions.

- [docs/governance/dte_instructions.md](../governance/dte_instructions.md)

## Closed World Rule

Treat the bundle as a closed world.

- Do not browse the web.
- Do not assume files exist unless you can locate them in the bundle.
- If you need information that is not in the bundle, say so explicitly and propose a concrete change via a proposal.

## How to Answer

When answering questions:

- Cite internal bundle paths (for example: `site/index.html`, `site/dao_stakeholders/index.html`, `machine/dao_stakeholders/view.yaml`).
- Prefer concrete, inspectable statements over speculation.
- If there are multiple relevant files, list them in a stable order (lexicographic).

## Grounding checklist (must apply)

- Every claim must cite a DT URL or repo-relative path. If not, mark it as **assumption/evidence gap**.

## How to End the Session (Draft a Proposal)

When the Q/A session ends, draft a concrete proposal folder under `proposals/`.

**Stakeholder confirmation is required before persisting a proposal.** If confirmation is not explicit, pause and request it.

Final Session Closeout must be convertible into the DAO proposal schema:
- [docs/dao/dao_proposal_schema.yaml](../dao/dao_proposal_schema.yaml)

Populate explicitly:
- `grounding.portal_references`
- `grounding.implementation_references`

Reject proposals that lack file-level grounding unless marked as an evidence gap (`evidence_gap.present: true`).

Standardized end-of-session output:

A) DT portal recommendations
B) eudr-dmi-gil evidence/mapping/code change recommendations
C) testing/regeneration/runbook recommendations

## Implementation inspection summaries

These mirrors are for inspection only. All changes must be proposed against authoritative files in eudr-dmi-gil.

- [docs/implementation_mirror/report_pipeline.md](../implementation_mirror/report_pipeline.md)
- [docs/implementation_mirror/dependency_model.md](../implementation_mirror/dependency_model.md)
- [docs/implementation_mirror/report_outputs.md](../implementation_mirror/report_outputs.md)

Create:

```
proposals/
  SCP-YYYY-NNN-<slug>/
    proposal.yaml
    evidence_refs.yaml
    claimed_impact.md
```

### proposal.yaml (template)

```yaml
schema_version: "1.0"
proposal_id: "SCP-YYYY-NNN-<slug>"
view: "dao_stakeholders"
status: "DRAFT"
title: "<short title>"
authors:
  - name: "<name>"
    role: "stakeholder"
summary: |
  <1-3 paragraphs explaining what is changing and why.>

problem_statement: |
  <what is wrong/missing/unclear today?>

requested_change: |
  <what should be added/removed/rewritten?>

acceptance_criteria:
  - "<objective, testable criterion>"

bundle_paths_cited:
  - "<path inside bundle>"

notes_for_reviewers: |
  <how a reviewer can verify using only the bundle.>
```

### evidence_refs.yaml (template)

```yaml
schema_version: "1.0"
proposal_id: "SCP-YYYY-NNN-<slug>"
refs:
  - path: "site/..."
    reason: "<why this file matters>"
```

### claimed_impact.md (template)

```markdown
# Claimed Impact

## Who benefits
- <stakeholder group>

## What improves
- <clarity / portability / auditability>

## Risks
- <what could break?>

## How to validate (bundle-only)
- Open: <path>
- Check: <what to confirm>

## See also

- [README.md](../../README.md)
- [docs/dao/dao_proposal_schema.yaml](../dao/dao_proposal_schema.yaml)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
```

## See also

- [docs/governance/dte_instructions.md](../governance/dte_instructions.md)
- [docs/INSPECTION_INDEX.md](../INSPECTION_INDEX.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
