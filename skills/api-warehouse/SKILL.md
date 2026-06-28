---
name: api-warehouse
description: >
  Use whenever the user wants to ingest an API end to end, go from API docs to
  warehouse, or build a full ingestion pipeline from documentation — even if
  they don't name a step. Trigger phrases: "ingest an API end to end",
  "API to warehouse", "build an ingestion pipeline from API docs", "set up a
  full pipeline from this API", or any request to take API documentation all
  the way through to a scheduled warehouse load.
---

# api-warehouse — Full API Ingestion Orchestrator

## Security Rule

Secrets (API tokens, credentials, connection strings) must travel via
environment variables, never typed into chat. Reference them by name
(e.g. `MY_API_TOKEN`) and store values in `.env` or a secrets manager.
See `references/security.md` for the full policy.

## Scope Guard

**RAW LANDING ONLY.** This pipeline writes raw API responses to the destination
unchanged. No transformation, renaming, or modelling happens here. Downstream
work (dbt, etc.) is out of scope.

---

## The Loop

Five step-skills run in order:

```
connect → assess → [CHECKPOINT] → land → validate → schedule
```

This orchestrator calls each step in sequence and pauses at the checkpoint
after `assess` so the user can review findings and confirm scope before any
data moves. Each step runs its own eval loop per
[`../../references/running-evals.md`](../../references/running-evals.md).
After all steps complete, run this skill's own `EVALS.md` and append any
notable run quirks to `MEMORY.md`. Apply the prose standards in
[`../../references/anti-slop.md`](../../references/anti-slop.md) to any
generated summaries.

---

## Step 1 — connect

Run the `connect` skill to verify credentials and destination reachability.

Invoke: `/connect`

Tests that the API token is valid, the base URL responds, and the destination
warehouse accepts writes. No data is moved. The step ends with a pass/fail
status for each check. Do not proceed until all checks pass.

---

## Step 2 — assess

Run the `assess` skill against the API documentation.

Invoke: `/assess`

Reads the API docs, lists endpoints, determines pagination style, checks
incremental support, fetches real sample rows, writes `endpoints.json`, and
renders `assessment.html`.

---

## CHECKPOINT — Review Before Landing

After `assess` completes, stop and tell the user:

> `assessment.html` is ready. Open it, review the endpoint list, incremental
> verdict, and estimated volume. Confirm scope before we proceed to `land` —
> share it with your client for sign-off if needed.

Do not run `land` until the user explicitly confirms scope. This is where
misunderstandings about which endpoints to include, key fields, or load
strategy (full-replace vs incremental) get caught.

---

## Step 3 — land

Once the user confirms scope, run the `land` skill.

Invoke: `/land`

Reads `endpoints.json`, calls `build_rest_api_config` to build the dlt
pipeline config, runs the pipeline to fetch all in-scope endpoints, and writes
raw rows to the destination as configured in `references/destinations.md`.
Raw landing only — no transformation.

---

## Step 4 — validate

Run the `validate` skill immediately after `land` completes.

Invoke: `/validate`

Calls `render_validation` to check row counts, schema presence, and freshness;
produces a validation report; notes any checks skipped because they could not
be automated. Fix any failures before scheduling.

---

## Step 5 — schedule

Once validation passes, run the `schedule` skill.

Invoke: `/schedule`

Packages the pipeline into a container image using the project `Dockerfile`,
generates a platform-specific deploy manifest (Cloud Run, Azure Container Apps,
or AWS ECS), and registers the cron schedule. After this step, follow
`deploy/<platform>.md` to run the pipeline on the agreed cadence yourself —
v1 produces a deploy-ready bundle, it does not auto-deploy.

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
