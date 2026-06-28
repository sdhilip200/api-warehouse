---
name: api-warehouse
description: >
  Use this skill when the user wants to ingest an API end to end, move API data
  to a warehouse, or build an ingestion pipeline from API docs.
  Trigger phrases include: "ingest an API end to end", "API to warehouse",
  "build an ingestion pipeline from API docs", "set up a full pipeline from this
  API", or any request to take API documentation all the way through to a
  scheduled warehouse load.
---

# api-warehouse — Full API Ingestion Orchestrator

## Scope Guard

**RAW LANDING ONLY.** This pipeline lands raw API responses into the destination
as-is. No transformation, renaming, or modelling happens here. Downstream
transformation (dbt, etc.) is out of scope for this skill.

## Security Rule

Secrets (API tokens, credentials, connection strings) must be provided via
environment variables — never typed into chat. Reference them by their env-var
name (e.g. `MY_API_TOKEN`) and store values in `.env` or your secrets manager.
See `references/security.md` for the full security policy.

---

## The Loop

This skill runs five step-skills in order:

```
connect → assess → [CHECKPOINT] → land → validate → schedule
```

Each step is a separate skill. This orchestrator calls them in sequence and
pauses at the checkpoint after `assess` so the user can review the assessment
and confirm scope (or obtain client sign-off) before any data moves.

---

## Step 1 — connect

Run the `connect` skill to verify credentials and destination reachability.

> Invoke: `/connect`

What it does: tests that the API token is valid, the base URL responds, and the
destination warehouse accepts writes. No data is moved. The step ends with a
green/red status for each check.

Do not proceed until `connect` reports all checks passing.

---

## Step 2 — assess

Run the `assess` skill against the API documentation.

> Invoke: `/assess`

What it does: reads the API docs, lists endpoints, determines pagination style,
checks incremental support, fetches real sample rows, writes `endpoints.json`,
and renders `assessment.html`.

---

## CHECKPOINT — Review Before Landing

After `assess` completes, **stop and tell the user**:

> `assessment.html` is ready. Please open it, review the endpoint list,
> incremental verdict, and estimated volume. Confirm the scope before we
> proceed to `land` — share it with your client for sign-off if needed.

Do **not** run `land` until the user explicitly confirms scope. This is the
moment to catch misunderstandings about which endpoints to include, key fields,
or load strategy (full-replace vs incremental).

---

## Step 3 — land

Once the user confirms scope, run the `land` skill.

> Invoke: `/land`

What it does: reads `endpoints.json`, calls `build_rest_api_config` to build
the dlt pipeline config, runs the pipeline to fetch all in-scope endpoints, and
writes raw rows to the destination as configured in `references/destinations.md`.
Raw landing only — no transformation.

---

## Step 4 — validate

Run the `validate` skill immediately after `land` completes.

> Invoke: `/validate`

What it does: calls `render_validation` to check row counts, schema presence,
and freshness; produces a validation report; notes any checks that were skipped
because they could not be automated. Review the report and fix any failures
before scheduling.

---

## Step 5 — schedule

Once validation passes, run the `schedule` skill.

> Invoke: `/schedule`

What it does: packages the pipeline into a container image using the project
`Dockerfile`, generates a platform-specific deploy manifest (Cloud Run, Azure
Container Apps, or AWS ECS), and registers the cron schedule. After this step
the pipeline runs automatically on the agreed cadence.

---

## Quick Reference

| Step | Skill | Key output |
|------|-------|-----------|
| 1 | connect | credential + destination health |
| 2 | assess | `endpoints.json`, `assessment.html` |
| CHECKPOINT | — | user/client sign-off |
| 3 | land | raw rows in warehouse |
| 4 | validate | validation report |
| 5 | schedule | deployed, scheduled container |
