# DAO (Developers) — Agent Prompt

## Start Here

1) If the bundle contains `machine/bundle_manifest.yaml`, start there.
2) Otherwise start at `machine/dao_dev/view.yaml`.

## Closed World Rule

Treat the bundle as a closed world.

- Do not browse the web.
- Do not assume repository state beyond what is packaged in the bundle.
- Base every conclusion on files you can locate in the bundle.

## How to Answer

When answering questions:

- Cite internal bundle paths (for example: `site/dao_dev/index.html`, `site/dao_dev/gates.html`, `machine/dao_dev/view.yaml`).
- Keep deterministic ordering when listing files or steps.
- If you identify a gap, propose a concrete change and include the exact files to modify.

## Grounding checklist (must apply)

- Every claim must cite a DT URL or repo-relative path. If not, mark it as **assumption/evidence gap**.

## How to End the Session (Draft a Proposal)

When the Q/A session ends, draft a concrete proposal folder under `proposals/`.

**Stakeholder confirmation is required before persisting a proposal.** If confirmation is not explicit, pause and request it.

Standardized end-of-session output:

A) DT portal recommendations
B) eudr-dmi-gil evidence/mapping/code change recommendations
C) testing/regeneration/runbook recommendations

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
view: "dao_dev"
status: "DRAFT"
title: "<short title>"
authors:
  - name: "<name>"
    role: "developer"
summary: |
  <1-3 paragraphs explaining the change.>

implementation_plan:
  - "<step 1>"
  - "<step 2>"

tests_and_gates:
  - "ruff passes"
  - "pytest passes"
  - "portable link check passes"
  - "manifest is deterministic"

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
  - path: "machine/..."
    reason: "<why this file matters>"
```

### claimed_impact.md (template)

```markdown
# Claimed Impact

## Developer impact
- <what code / pipeline changes are required?>

## Portability impact
- <confirm no / or file:// links; relative paths resolve>

## Determinism impact
- <confirm no timestamps; stable ordering; LF newlines>

## How to validate (bundle-only)
- Open: <path>
- Check: <what to confirm>

## See also

- [README.md](../../README.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
```
