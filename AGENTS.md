# api-warehouse — agent instructions

This repository is the `api-warehouse` coding-agent plugin. It works in **Claude Code** and **Codex** (and other agents that read `AGENTS.md` + load `skills/`). The skills are plain Markdown and platform-neutral; this file tells any agent how to use them.

## What this plugin does

Reads any API's documentation and takes it to raw data in a warehouse, with a client-ready assessment and validation. Raw landing only — transformation is out of scope.

## Skills (in `skills/`)

Each skill is a folder with a `SKILL.md` (instructions), an `EVALS.md` (objective self-checks), and a `MEMORY.md` (API-specific quirks learned over time).

| Skill | Use it to |
|-------|-----------|
| `api-warehouse` | Run the whole loop end to end (orchestrator) |
| `connect` | Set up API auth securely (env vars / `.dlt/secrets.toml`) and smoke-test reachability |
| `assess` | Read the docs: endpoints, auth, pagination, evidence-backed incremental verdict; pull samples; write `assessment.html` + `endpoints.json` |
| `land` | Generate and run a dlt pipeline; land raw data into the chosen destination |
| `validate` | Best-effort control-total reconciliation of source vs loaded data; write `validation.html` |
| `schedule` | Package a deploy-ready bundle (Dockerfile + per-platform deploy steps) |

The loop: `connect → assess → [human checkpoint] → land → validate → schedule`. Pause at the checkpoint so the user reads `assessment.html` and confirms scope (one-time vs incremental, which endpoints, destination) before any data moves.

## How to invoke

- **Claude Code:** the skills register as `/connect`, `/assess`, `/land`, `/validate`, `/schedule`, `/api-warehouse`.
- **Codex / other agents:** when the user's request matches a skill's purpose (e.g. "ingest this API into my warehouse: <docs URL>"), read that skill's `SKILL.md` and follow it. Start with `skills/api-warehouse/SKILL.md` for an end-to-end request.

## Non-negotiable rules (every skill enforces these)

- **Secrets** are read only from environment variables or `.dlt/secrets.toml`, referenced by name. Never hardcode, echo, log, or write a secret value into generated code, reports, or Docker images. Warehouse connections use dlt's native connectors, not MCP.
- **Raw landing only.** Do not add transformation/modeling.
- **Honesty.** The incremental verdict must cite evidence (a filter param or cursor field) or state a reason; validation marks unverifiable checks `skipped`, never a fabricated pass; reject input that is not API documentation.

## Python dependencies

The `land` and `validate` steps use the bundled `api_warehouse/` library and dlt:

```bash
pip install "dlt[duckdb]"                                  # add bigquery/snowflake/postgres extras as needed
pip install "git+https://github.com/sdhilip200/api-warehouse"   # the api_warehouse library the skills import
```

## Platform portability note (eval loop)

`references/running-evals.md` describes a self-grading loop that "spins up a separate grader agent" to run a skill's `EVALS.md` against its output. On platforms with subagents (Claude Code), use a separate agent so the grader has a clean context. On platforms without subagents (e.g. Codex), run the same checklist inline in a fresh reasoning pass, then revise the artifact if any check fails. The behavior is identical; only the isolation mechanism differs.
