# Digital Twin – Link Registry (Inspection Surface)

This registry enumerates canonical, publicly accessible Digital Twin
HTML artefacts that may be inspected by stakeholders and AI agents
without URL synthesis.

These links belong to the **non-authoritative inspection surface**.

Base URLs:
- `DT_BASE_URL_PUBLIC=https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/`
- `DT_BASE_URL_AI_SAFE=https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/`

AI-safe rule:
- Use `DT_BASE_URL_AI_SAFE` when DNS/policy blocks `DT_BASE_URL_PUBLIC`.
- Do **not** use `https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/` because it redirects and is not an approved AI-safe inspection base.

---

## Mandatory entrypoint

- Digital Twin home (public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/index.html

- Digital Twin home (AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/index.html

---

## AOI Reports

- AOI reports index (runs list, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/index.html

- AOI reports index (runs list, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/index.html

- Example with cadastre-based validation in Estonia (HTML, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/example/report.html

- Example with cadastre-based validation in Estonia (HTML, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/example/report.html

- Example with cadastre-based validation in Estonia (JSON, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/example/estonia_aoi_report.json

- Example with cadastre-based validation in Estonia (JSON, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/example/estonia_aoi_report.json

- Example of mixed crop in Latin America (HTML, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/latin_america/report.html

- Example of mixed crop in Latin America (HTML, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/latin_america/report.html

- Example of mixed crop in Latin America (JSON, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/latin_america/latin_america_aoi_report.json

- Example of mixed crop in Latin America (JSON, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/latin_america/latin_america_aoi_report.json

- Example of coffee in SE Asia (HTML, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/se_asia/report.html

- Example of coffee in SE Asia (HTML, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/se_asia/report.html

- Example of coffee in SE Asia (JSON, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/se_asia/se_asia_aoi_report.json

- Example of coffee in SE Asia (JSON, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/se_asia/se_asia_aoi_report.json

- Example of cocoa in West Africa (HTML, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/west_africa/report.html

- Example of cocoa in West Africa (HTML, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/west_africa/report.html

- Example of cocoa in West Africa (JSON, public):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin/site/aoi_reports/runs/west_africa/west_africa_aoi_report.json

- Example of cocoa in West Africa (JSON, AI-safe):
  https://georgemadlis.github.io/eudr-dmi-gil-digital-twin-ai-mirror/site/aoi_reports/runs/west_africa/west_africa_aoi_report.json

---

## Navigation discipline

- Agents MUST prefer portal navigation when possible.
- This registry exists to prevent URL guessing failures in constrained environments.
- Presence in this file explicitly authorizes inspection.
