# Regulation Sources Registry

Purpose: record authoritative source snapshots (HTML/PDF) and their SHA-256 fingerprints without embedding the regulation text in this repository.

**Authority boundary:** This document provides inspectable mappings only. Authoritative acquisition logic and deterministic pipelines live in the implementation repository: https://github.com/GeorgeMadlis/eudr-dmi-gil

Server audit root: `/Users/server/audit/eudr_dmi`

| Source | URL | Local Path (server) | SHA256 | Notes |
|---|---|---|---|---|
| EUDR 2023/1115 — OJ (ELI) HTML | https://eur-lex.europa.eu/eli/reg/2023/1115/oj/eng | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_oj_eng.html` | TODO | Acquire via the workflow below; do not paste text into repo. |
| EUDR 2023/1115 — Consolidated HTML (2024-12-26) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02023R1115-20241226 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_consolidated_2024-12-26_en.html` | TODO | Acquire via the workflow below; do not paste text into repo. |
| EUDR 2023/1115 — CELEX PDF endpoint (32023R1115) | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1115 | `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/eudr_2023_1115_celex_32023R1115_en.pdf` | TODO | Acquire via the workflow below; hash whatever is stored after verification. |

## Operator workflow (WAF-safe)
Some EUR-Lex endpoints may be protected by WAF/login challenges depending on network and headers. This project does not attempt to bypass challenges.

Implementation reference (authoritative):
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/operations/environment_setup.md
- https://github.com/GeorgeMadlis/eudr-dmi-gil/blob/main/docs/operations/minio_setup.md

a) Open the link launcher in a browser:
- [docs/regulation/links.html](links.html)

b) If the browser can access the source, save the artefact to the exact server path shown on the launcher under `/Users/server/audit/eudr_dmi/regulation/...`.

c) Run the acquisition tool to verify non-empty files, compute SHA-256, and update registries:

```sh
python tools/regulation/acquire_and_hash.py --verify
```

Optional: if your browser session is required and you can export cookies, see [docs/operations/secrets_handling.md](../operations/secrets_handling.md) and run:

```sh
python tools/regulation/acquire_and_hash.py --fetch --cookie-jar /Users/server/secrets/eudr_dmi/eurlex_cookies.txt
```

## How to mirror EUR-Lex sources (deterministic, audit-grade)
This repository includes a deterministic “EUR-Lex mirror” for CELEX:32023R1115 that writes a run folder with hashes and metadata.

Note: https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32023R1115 is treated as an entry point to the EUDR “digital twin”. Re-run the mirror whenever this entry point (or the underlying regulation artefacts) change.

WAF note: LSU can be blocked in headless/automated environments. The mirror records an explicit entrypoint watch file so we still get a deterministic change signal even when LSU is unreachable.

Command:

```sh
python scripts/fetch_eurlex_eudr_32023R1115.py \
	--out /Users/server/audit/eudr_dmi/regulation/eudr_2023_1115 \
	--date 2026-01-21
```

Output folder:
- `audit/eudr_dmi/regulation/eudr_2023_1115/<YYYY-MM-DD>/`

What to check:
- Expected files in the run folder:
	- `metadata.json` (machine-readable record of per-source status, headers when available, and hashes)
	- `manifest.sha256` (sorted; covers stored artefacts + metadata)
	- `summary.html`
	- `lsu_entry.html` (EUDR digital twin entry point; when reachable)
	- `regulation.pdf`
	- Optional when accessible: `regulation.html`, `eli_oj.html`
	- Optional on failures: `fetch.log`
- Digital twin watch outputs:
	- `entrypoint_status.json` records LSU reachability and evidence.
		- If LSU is reachable (`http_status=200`), evidence includes `lsu_entry_sha256` (hash of `lsu_entry.html`) and an extracted `lsu_updated_on` date if present.
		- If LSU is not reachable (e.g. WAF), evidence includes a fallback fingerprint derived from the most stable available endpoints (PDF/HTML/ELI hashes and headers when available).
	- `metadata.json` includes a top-level `needs_update` boolean computed by comparing this run’s entrypoint watch fingerprints to the latest prior run folder under the same `--out` base.
	- When `needs_update=true`, the mirror writes `digital_twin_trigger.json`. Downstream “digital twin” jobs should watch for this file.
- If EUR-Lex blocks requests (HTTP 202 / WAF challenge), the run is recorded as `status=partial` and the error is captured in metadata (and `fetch.log` when present).

Expected SHA256SUMS paths (server):
- `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/SHA256SUMS.txt`
- `/Users/server/audit/eudr_dmi/regulation/guidance/SHA256SUMS.txt` (if guidance PDFs are added)

## Scheduled watcher (daily)
For downstream automation (cron/launchd/GitHub Actions), use the watcher wrapper which runs the mirror and exits with a meaningful code:

```sh
python scripts/watch_eurlex_eudr_32023R1115.py \
	--out /Users/server/audit/eudr_dmi/regulation/eudr_2023_1115
```

Exit codes:
- `0` = no change (`needs_update=false`)
- `2` = change detected / update needed (`needs_update=true` with a strong fingerprint change)
- `3` = partial / upstream blocked / uncertain (e.g. LSU WAF challenge without a confident fingerprint diff)

## Manual verification checklist
See [docs/regulation/mirror_manual_checklist.md](mirror_manual_checklist.md).

## How to propose changes

Use the DAO stakeholder prompt to submit questions or change proposals:
- [docs/agent_prompts/dao_stakeholders_prompt.md](../agent_prompts/dao_stakeholders_prompt.md)

## See also

- [README.md](../../README.md)
- [docs/governance/dte_instructions.md](../governance/dte_instructions.md)
- [docs/governance/roles_and_workflow.md](../governance/roles_and_workflow.md)
- [docs/views/digital_twin_view.md](../views/digital_twin_view.md)
- https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/
