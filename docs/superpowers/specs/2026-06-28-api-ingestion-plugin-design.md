# Design Spec — API Ingestion Plugin (`api-warehouse`)

- **Date:** 2026-06-28
- **Author / maintainer:** Dhilip Subramanian — GitHub [@sdhilip200](https://github.com/sdhilip200)
- **Status:** Design — pending user review
- **License (intended):** MIT

---

## 1. One-line pitch

> **Point a coding agent at any API's documentation → get a client-ready assessment, sample data, and raw data landed in your warehouse — securely, with validation.**

A Claude Code plugin (also usable as a standalone skill in other agents) that automates the **discovery + raw-ingestion** half of a data engineer's job. It deliberately stops at *raw landing*; transformation is a separate downstream pipeline and is out of scope.

---

## 2. Problem & positioning

A data engineer handed a new API repeatedly does the same manual work: read the docs, figure out auth/pagination/incremental support, pull sample data for the client, then build a pipeline that lands raw data in a warehouse and reconcile the numbers. This is intelligent, repetitive, and unautomated.

### Why existing tools don't cover this

| Tool | What it does | What it leaves to a human |
|------|--------------|---------------------------|
| **dlt** ([dlt-hub/dlt](https://github.com/dlt-hub/dlt), 5.5k★, Apache-2.0) | The *load engine*: schema inference, incremental, schema evolution, destinations (BigQuery, Snowflake, Postgres, Azure, DuckDB). Declarative config. | **Reading the docs and writing the config** (base URL, auth, pagination, primary key, cursor). `dlt-init-openapi` automates this *only* from a machine-readable OpenAPI spec — useless for the common case of HTML-only docs. |
| **printing-press** ([mvanhorn/cli-printing-press](https://github.com/mvanhorn/cli-printing-press)) | Generates an agent-native **CLI + MCP** to *call* an API, from any spec/site/HAR. | Not a warehouse-landing pipeline; no schema-evolving incremental load into a warehouse; no DE assessment/validation deliverable. |

### Our wedge (the unoccupied lane)

The **brain** that reads *human* API docs and produces (a) the config dlt forces you to hand-write, plus (b) the **data-engineering deliverables** no tool packages:

1. A **client-ready API Assessment report** (endpoints, auth, pagination, incremental verdict, rate limits, volume estimate).
2. **Sample data** for client sign-off.
3. A **dlt raw-landing pipeline** into the chosen destination.
4. A **validation / control-total report** reconciling source vs loaded data.
5. A **deploy-ready bundle** for scheduling.

> Positioning rule for the README: lead with *"any API docs → assessment + raw data in your warehouse,"* **not** *"connect to any API"* (already done by printing-press). The edge is the **DE deliverable**, not the act of connecting.

---

## 3. Goals & non-goals

### Goals
- Work from **human-readable API docs** (URL or pasted), not just OpenAPI specs.
- Be **runtime-adaptive** — paste any docs link and get value in-session; no pre-baked per-API connectors.
- Treat **security as a first-class feature**: secrets via environment variables / `.dlt/secrets.toml`, never hardcoded, never echoed, never stored by the skill.
- Produce **honest, confidence-stated outputs**: best-effort validation that admits gaps; evidence-backed incremental verdict; reject inputs that aren't API docs.
- Ship as a **professional, contributor-friendly open-source plugin**.

### Non-goals (v1)
- **No transformation** — raw landing only. Modeling/cleaning is a separate downstream pipeline.
- **No actually-deploying into the user's cloud** — v1 generates deploy-ready artifacts + instructions; the user runs the deploy. (Auto-deploy = v2.)
- **No destination connection via MCP** — warehouse loading uses dlt connectors + credentials from the user's own secrets store.

---

## 4. Target users

- Data engineers / analytics engineers doing API ingestion (consulting or in-house).
- Their typical destinations: **BigQuery, Snowflake, Postgres, Azure SQL, Microsoft Fabric, or blob storage** (Parquet/CSV in S3/GCS/Azure Blob).

---

## 5. Architecture

### 5.1 Shape
An MIT-licensed **Claude Code plugin**, modeled on the proven structure of
[compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) (22.1k★) and
[frontend-slides](https://github.com/zarazhangrui/frontend-slides) (23.5k★):

- `skills/` — one folder per skill, each with a `SKILL.md`.
- `.claude-plugin/` + `plugin.json` — manifest, installable via `/plugin marketplace add`.
- Supporting reference docs (`references/`) so contributors can add patterns without touching skill logic.

### 5.2 The loop (6 skills + 1 orchestrator)

```
                  API docs URL or pasted docs
                              │
                              ▼
  ┌───────────────────────────────────────────────────────────┐
  │ 0. (guard, inside `assess`) Is this really API docs?       │
  │    If not → STOP: "This doesn't look like API documentation"│
  └───────────────────────────────────────────────────────────┘
                              │
  ┌───────────────────────────────────────────────────────────┐
  │ 1. connect   secure auth setup (env var / secrets.toml)    │
  │              + smoke test (is the API reachable?)          │
  │              OUTPUT: connectivity check                    │
  └───────────────────────────────────────────────────────────┘
                              │
  ┌───────────────────────────────────────────────────────────┐
  │ 2. assess    probe endpoints; detect incremental support   │
  │              (evidence-backed verdict); estimate volume;   │
  │              intent interview (how much? one-time vs        │
  │              incremental?); pull sample rows               │
  │              OUTPUT: assessment.html + endpoints.json       │
  │                      + samples/*.json|csv                   │
  └───────────────────────────────────────────────────────────┘
                  ── CHECKPOINT: user reads report,
                     confirms scope / client sign-off ──
  ┌───────────────────────────────────────────────────────────┐
  │ 3. land      pick destination (secure creds); generate a   │
  │              dlt rest_api pipeline; run it                  │
  │              OUTPUT: pipeline code + RAW data loaded        │
  └───────────────────────────────────────────────────────────┘
                              │
  ┌───────────────────────────────────────────────────────────┐
  │ 4. validate  control-total reconciliation (best-effort):   │
  │              row count, numeric sum/min/max, distinct       │
  │              categories, timestamp min/max, null rates      │
  │              OUTPUT: validation.html                        │
  └───────────────────────────────────────────────────────────┘
                              │
  ┌───────────────────────────────────────────────────────────┐
  │ 5. schedule  package deploy-ready bundle (Dockerfile +     │
  │              schedule config + per-platform deploy steps:  │
  │              Cloud Run / Azure / AWS). User runs deploy.   │
  │              OUTPUT: deployable bundle                     │
  └───────────────────────────────────────────────────────────┘

  + orchestrator: runs 1→5 with the checkpoint pause.
```

### 5.3 Division of labor
- **The skills = the brain.** Read docs → make decisions → write config + reports.
- **dlt = the hands.** Reliable load, schema inference/evolution, incremental state, per-destination connectors.
- The `assess` step produces exactly the inputs dlt normally forces a human to hand-write.

---

## 6. Skill details

### 6.1 `connect`
- **Input:** API base/auth info derived from docs; user-supplied secret.
- **Behavior:** Instruct the user to store the key as an **environment variable** (or `.dlt/secrets.toml`). Never print or persist the secret. Run a minimal authenticated request as a smoke test.
- **Output:** Connectivity check — reachable? auth valid? — in plain language.

### 6.2 `assess`
- **Step 0 — input guard:** Confirm the input is genuinely API documentation (endpoints, methods, auth visible). If not, **stop with a clear message**.
- **Endpoint inventory:** list endpoints, methods, params, response fields & types.
- **Capability detection:**
  - **Pagination** style (offset/page/cursor/link-header).
  - **Incremental verdict (the "senior DE" check):** thoroughly hunt for `updated_since` / `modified_after` / `since` / `start_date` params, sortable `updated_at` fields, cursors, change feeds, webhooks. Return **YES (with evidence) or NO (with reason)** — never a guess presented as fact.
  - **Rate limits** & auth type.
  - **Volume estimate** (e.g., earliest data available, approximate record counts when discoverable).
- **Intent interview:** how much data to extract; one-time raw load vs incremental pipeline (reconciled against the incremental verdict).
- **Sample pull:** a few real rows per key endpoint.
- **Output:** `assessment.html` (client-ready), `endpoints.json` (machine-readable for `land`), `samples/`.

### 6.3 `land`
- **Input:** `endpoints.json`, chosen destination, secure credentials (env/secrets.toml).
- **Destinations:** BigQuery, Snowflake, Postgres, Azure SQL, blob (Parquet/CSV) — via dlt connectors.
- **Behavior:** Generate a small, readable **dlt `rest_api` pipeline** from the assessment; run it; land **raw, untransformed** data.
- **Output:** pipeline code (committed to the user's project) + raw data in the destination.

### 6.4 `validate`
- **Best-effort control totals** (states which checks are/aren't possible):
  - Row count: source (when the API exposes totals) vs loaded.
  - Numeric columns: sum / min / max.
  - Categorical/text columns: distinct value counts & breakdown.
  - Timestamp columns: min/max range (caught missing recent/old records).
  - Null rates per column (spikes flag parsing/mapping bugs).
- **Output:** `validation.html`. Explicitly states when source-side numbers are unavailable and that it validated by load success + sampling instead.

### 6.5 `schedule` (option A — deploy-ready only)
- **Output:** `Dockerfile`, a schedule/cron config, and copy-paste deploy instructions for **Google Cloud Run / Azure / AWS**. The user performs the final deploy. (Auto-deploy = v2.)

### 6.6 `orchestrator`
- Runs `connect → assess → [checkpoint] → land → validate → schedule` end-to-end, pausing at the assessment checkpoint for human/client sign-off.

---

## 7. Security model (first-class)
- Secrets live in **environment variables** or **`.dlt/secrets.toml`** in the user's own environment.
- The skill **never** hardcodes, echoes, logs, or transmits secrets.
- Warehouse auth uses dlt's native credential handling (e.g., a BigQuery service-account JSON referenced from secrets), **not MCP**.
- Because the agent may run in the user's cloud, all reports and generated code are scrubbed of secret values.

---

## 8. Reports
- **Client-facing reports are HTML** (shareable, standalone, like frontend-slides' single-file output): `assessment.html`, `validation.html`.
- Machine-readable artifacts (`endpoints.json`) drive the next skill.

---

## 9. Professional GitHub presentation (star-worthy)

Modeled on compound-engineering & frontend-slides (both MIT, 20k+★):

- **README** that opens with the one-line pitch + an animated/GIF demo of *"paste docs link → assessment + loaded data."*
- **Clear positioning section** (the table in §2) — honest about dlt & printing-press; states the wedge.
- **Quick start:** `/plugin marketplace add https://github.com/sdhilip200/api-warehouse` then `/plugin install`.
- **One example walkthrough end-to-end** (e.g., a public API → Postgres) with screenshots of the HTML reports.
- **`CONTRIBUTING.md`** — how to add a new "pattern" (pagination/auth/destination) or a new skill, so contributors can extend without touching core logic.
- **`LICENSE` (MIT)**, badges, `docs/`, issue/PR templates.
- Branding/author: **[@sdhilip200](https://github.com/sdhilip200)**.

---

## 10. Naming (decided)
**`api-warehouse`** — repo `github.com/sdhilip200/api-warehouse`. Chosen for clarity: the name states the value (API → warehouse) directly.

---

## 11. Success criteria
- A user can paste an arbitrary public API's docs URL and, within one session, get: a correct assessment report, sample data, raw data landed in a chosen destination, and a validation report.
- The incremental verdict is evidence-backed and correct on at least the test APIs.
- Non-API input is rejected with a clear message.
- Secrets never appear in generated files or reports.
- README/CONTRIBUTING are polished enough that an external contributor can add a pagination pattern via PR.

---

## 12. Future (v2+)
- Actual auto-deploy/scheduling into Cloud Run/Azure/AWS.
- More destinations (Databricks/Delta, Microsoft Fabric first-class).
- Optional "generate downstream transformation skeleton" (still separate from raw landing).
- Multi-agent support (Cursor/Codex/Copilot) like compound-engineering.
