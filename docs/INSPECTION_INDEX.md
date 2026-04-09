# Inspection Index (DTE Cross-Repo Router)

This document is the Digital Twin side of the DTE reading order.

It does not replace the authoritative implementation index in
`eudr-dmi-gil/docs/INSPECTION_INDEX.md`. Instead, it tells DTE which repo to
open next depending on the question being asked.

## Start here

For any governance or inspection session:

1. Open `docs/dte_instructions.md`.
2. Open `docs/DT_LINK_REGISTRY.md`.
3. Open `eudr-dmi-gil/docs/INSPECTION_INDEX.md`.
4. Open the relevant public Digital Twin artefact.
5. For portal UX, chat, or privacy-boundary questions, switch to:
   `eudr-client-portal` docs listed below.

## Authority boundary

- `eudr-dmi-gil-digital-twin` is authoritative for:
  - published inspection entrypoints and navigable public URLs
  - DAO-facing inspection guidance and proposal framing
  - public, non-authoritative mirrors of implementation concepts
- `eudr-dmi-gil` is authoritative for:
  - implementation behavior
  - evidence contracts and bundle layout
  - deterministic generation and regeneration
  - dependency registries and tests
- `eudr-client-portal` is authoritative for:
  - portal workflow and UX
  - private/public chat routing
  - run-detail behavior, bundle ingestion, and privacy boundaries

## Mandatory DTE path

When answering a public-inspection question:

1. Open the public artefact through the Digital Twin.
2. Cite the DT URL or DT repo path for what is publicly visible.
3. Opened-session precondition: `eudr-dmi-gil/docs/INSPECTION_INDEX.md` must
   already be open before any implementation recommendation is made.
4. If a recommendation touches portal behavior, map it to the relevant
   `eudr-client-portal` doc.

If the authoritative implementation index was not opened in the session, or if
you cannot map the recommendation to one of those repos, mark it as an
**Evidence gap**.

## Question-to-doc routing

### Public AOI inspection and run navigation

Open these first:

- `docs/dte_instructions.md`
- `docs/DT_LINK_REGISTRY.md`
- `README.md`

Helpful mirrors:

- `docs/implementation_mirror/report_outputs.md`
- `docs/views/task_view.md`

Then switch to authoritative implementation docs for contract details:

- `eudr-dmi-gil/docs/reports/README.md`
- `eudr-dmi-gil/docs/reports/runbook_generate_aoi_report.md`

### Evidence sufficiency and policy mapping

Open these first:

- `docs/regulation/policy_to_evidence_spine.md`
- `docs/dao/proposal_schema.md`
- `docs/agent_prompts/dao_stakeholders_prompt.md`
- `docs/agent_prompts/dao_dev_prompt.md`

Then switch to implementation docs for grounded change targets:

- `eudr-dmi-gil/docs/INSPECTION_INDEX.md`
- `eudr-dmi-gil/docs/governance/roles_and_workflow.md`

### Dependency or regulation-source questions

Open these first:

- `docs/regulation/sources.md`
- `docs/implementation_mirror/dependency_model.md`
- `docs/views/digital_twin_view.md`

Then switch to authoritative implementation docs:

- `eudr-dmi-gil/docs/dependencies/README.md`
- `eudr-dmi-gil/docs/dependencies/sources.md`
- `eudr-dmi-gil/docs/architecture/dependency_register.md`

### Determinism, pipeline, and rerun questions

Open these first:

- `docs/views/agentic_view.md`
- `docs/views/digital_twin_view.md`
- `docs/implementation_mirror/report_pipeline.md`

Then switch to authoritative implementation docs:

- `eudr-dmi-gil/docs/architecture/decision_records/0001-report-pipeline-architecture.md`
- `eudr-dmi-gil/docs/reports/runbook_generate_aoi_report.md`

### Portal behavior, private/public chat, and user workflow questions

These are not resolved in the Digital Twin repo alone. Switch to
`eudr-client-portal` and open:

- `eudr-client-portal/README.md`
- `eudr-client-portal/docs/eudr_report_current_state.md`
- `eudr-client-portal/docs/ui/aoi_run_workflow.md`
- `eudr-client-portal/docs/architecture/public_private_knowledge_strategy.md`
- `eudr-client-portal/docs/architecture/llm_topology.md`
- `eudr-client-portal/docs/skills/02_public_inspector_chat.md`
- `eudr-client-portal/docs/skills/03_private_inspector_chat.md`

### Question-specific EUDR and report-answering references

For targeted answer support, use these portal knowledge docs:

Public:

- `eudr-client-portal/docs/eudr/summary.md`
- `eudr-client-portal/docs/skills/chat-skills/public/04_commodity_operator_applicability.md`
- `eudr-client-portal/docs/skills/chat-skills/public/05_country_risk_dds_workflow.md`
- `eudr-client-portal/docs/skills/chat-skills/public/06_reading_demo_reports.md`

Private/run-scoped:

- `eudr-client-portal/docs/skills/chat-skills/private/07_bundle_manifest_cross_reference.md`
- `eudr-client-portal/docs/skills/chat-skills/private/08_fail_triage.md`
- `eudr-client-portal/docs/skills/chat-skills/private/09_metrics_interpretation.md`

These improve answer quality and routing, but factual claims still need grounding
in opened DT artefacts or authoritative implementation docs.

## Core documents in this repo

### Canonical DTE session docs

- `docs/dte_instructions.md`
- `docs/DT_LINK_REGISTRY.md`
- `docs/dao/proposal_schema.md`

### Public inspection views

- `docs/views/digital_twin_view.md`
- `docs/views/task_view.md`
- `docs/views/agentic_view.md`

### Regulation and traceability

- `docs/regulation/policy_to_evidence_spine.md`
- `docs/regulation/sources.md`

### Inspection-only mirrors

- `docs/implementation_mirror/report_pipeline.md`
- `docs/implementation_mirror/report_outputs.md`
- `docs/implementation_mirror/dependency_model.md`

### DAO prompting helpers

- `docs/agent_prompts/dao_stakeholders_prompt.md`
- `docs/agent_prompts/dao_dev_prompt.md`
- `docs/governance/roles_and_workflow.md`

## Cross-repo quick map

| Need | Start in DT repo | Then open |
|---|---|---|
| Public run URL or AOI navigation | `docs/DT_LINK_REGISTRY.md` | `eudr-dmi-gil/docs/reports/README.md` |
| Public evidence sufficiency review | `docs/regulation/policy_to_evidence_spine.md` | `eudr-dmi-gil/docs/INSPECTION_INDEX.md` |
| Proposal structure | `docs/dao/proposal_schema.md` | `eudr-dmi-gil/docs/governance/roles_and_workflow.md` |
| Pipeline understanding | `docs/implementation_mirror/report_pipeline.md` | `eudr-dmi-gil/docs/architecture/decision_records/0001-report-pipeline-architecture.md` |
| Portal chat or run-page behavior | `README.md` | `eudr-client-portal/docs/eudr_report_current_state.md` |

## Practical DTE notes

- Use this repo to anchor what is publicly inspectable.
- Use `eudr-dmi-gil` to ground implementation changes.
- Use `eudr-client-portal` to explain user-facing behavior and chat boundaries.
- If repo docs disagree on URL patterns or current public run sets, prefer:
  - `docs/dte_instructions.md`
  - `docs/DT_LINK_REGISTRY.md`
  - opened DT artefacts
  Then record any remaining mismatch as a documentation gap.
