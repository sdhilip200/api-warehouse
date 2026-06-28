# api-warehouse

[![CI](https://github.com/sdhilip200/api-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/sdhilip200/api-warehouse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Point a coding agent at any API's docs → client-ready assessment, sample data, and raw data landed in your warehouse — securely, with validation.**

---

## Demo

*Demo GIF coming soon — paste any API docs link and watch it produce an assessment + load data.*

---

## Why api-warehouse?

A data engineer handed a new API repeatedly does the same manual work: read the docs, figure out auth, pagination, and incremental support, pull sample data for the client, then build a pipeline that lands raw data in a warehouse and reconcile the numbers.

### Positioning vs existing tools

| Tool | What it does | What it leaves to a human |
|------|--------------|--------------------------|
| **dlt** ([dlt-hub/dlt](https://github.com/dlt-hub/dlt), 5k+ stars) | The *load engine*: schema inference, incremental, schema evolution, destinations (BigQuery, Snowflake, Postgres, DuckDB). | **Reading the docs and writing the config** (base URL, auth, pagination, primary key, cursor). `dlt-init-openapi` only works from machine-readable OpenAPI — useless for HTML-only docs. |
| **printing-press** | Generates an agent-native CLI + MCP to *call* an API from any spec/site/HAR. | Not a warehouse-landing pipeline; no schema-evolving incremental load; no DE assessment/validation deliverable. |
| **api-warehouse** (this) | The **brain** that reads *human* API docs and produces the config dlt forces you to hand-write, **plus** the data-engineering deliverables no other tool packages. | Transformation and downstream modeling — deliberately out of scope (raw landing only). |

**Our edge is not "connect to any API"** (printing-press already does that). The edge is the **data-engineering deliverable**: assessment + sample + validated raw landing.

---

## What you get

1. A **client-ready API Assessment report** (endpoints, auth, pagination, incremental verdict, rate limits, volume estimate).
2. **Sample data** rows for client sign-off.
3. A **dlt raw-landing pipeline** into your chosen destination (DuckDB, Postgres, BigQuery, Snowflake, …).
4. A **validation / control-total report** reconciling source vs loaded row counts.
5. A **deploy-ready bundle** for scheduling on Cloud Run, Azure Container Apps, or AWS ECS.

---

## Quick start

**Install the plugin:**

```
/plugin marketplace add https://github.com/sdhilip200/api-warehouse
/plugin install
```

**Run the full loop:**

```
/api-warehouse https://jsonplaceholder.typicode.com
```

Or run individual steps:

```
/connect https://jsonplaceholder.typicode.com
/assess https://jsonplaceholder.typicode.com
/land posts --destination duckdb
/validate
/schedule
```

---

## The loop

```
API docs URL or pasted docs
          │
          ▼
  [connect]   ── secure auth setup (env vars / .dlt/secrets.toml) + smoke test
          │
          ▼
  [assess]    ── probe endpoints; detect incremental support (evidence-backed);
               │  estimate volume; pull sample rows
               │  OUTPUT: assessment.html + endpoints.json + samples/*.json
          │
          ▼
  [checkpoint] ── present report to user; confirm intent (one-time vs incremental,
               │  which endpoints, destination)
          │
          ▼
  [land]      ── build dlt pipeline from endpoints.json; load raw data
               │  OUTPUT: rows in destination table
          │
          ▼
  [validate]  ── reconcile source count vs loaded count; emit validation.html
          │
          ▼
  [schedule]  ── generate deploy-ready Dockerfile + deploy instructions
               │  OUTPUT: deploy bundle (Cloud Run / Azure / ECS)
```

---

## Security promise

- **Secrets never leave your machine.** The plugin reads credentials from environment variables or `.dlt/secrets.toml` — it never echoes, logs, or stores secrets.
- `.dlt/secrets.toml` and `.env` are in `.gitignore` and `.dockerignore`.
- See [`references/security.md`](references/security.md) for the full security model.

---

## Scope guard (raw landing only)

api-warehouse deliberately stops at *raw landing*. Transformation, modeling, and cleaning are separate downstream pipelines. This is not a bug; it is a design constraint.

---

## Worked example

See [`examples/jsonplaceholder/README.md`](examples/jsonplaceholder/README.md) for a full end-to-end walkthrough: assess JSONPlaceholder → land `/posts` into DuckDB → validate.

---

## Reference docs

- [`references/auth-patterns.md`](references/auth-patterns.md) — supported auth patterns
- [`references/pagination-patterns.md`](references/pagination-patterns.md) — pagination detection
- [`references/incremental-detection.md`](references/incremental-detection.md) — cursor / watermark detection
- [`references/destinations.md`](references/destinations.md) — supported destinations
- [`references/security.md`](references/security.md) — security model

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

MIT © [@sdhilip200](https://github.com/sdhilip200)
