---
name: schedule
description: >
  Use whenever the user wants to schedule, deploy, or automate the pipeline —
  run it on a cron, package it for Cloud Run, Azure Container Apps, or AWS ECS/Fargate,
  or set up any recurring cloud execution. Trigger even if they don't say "schedule":
  phrases like "run it every day", "containerize the pipeline", "deploy to the cloud",
  "automate the pipeline", or "set up a job" all qualify.
---

# Schedule Skill

## What this skill does (v1)

Produces a deploy-ready bundle — a `Dockerfile`, a `.dockerignore`, a starter
`requirements.txt`, and platform-specific deployment instructions — inside a `deploy/`
directory the user can inspect and run themselves.

v1 does not auto-deploy. You run the commands. Auto-deploy is planned for v2.

Before writing any files, read `MEMORY.md` for platform-specific quirks that
have caught users before.

---

## Step 1 — Ask the user which platform and cron schedule

Ask both questions in one message:

> Which cloud platform would you like to deploy to?
> 1. Google Cloud Run (Cloud Run Job + Cloud Scheduler)
> 2. Azure Container Apps (Job with cron trigger)
> 3. AWS ECS (Fargate scheduled task + EventBridge)
>
> What cron schedule would you like? (e.g. `"0 6 * * *"` for 6 AM UTC daily)

Do not proceed until you have both answers.

---

## Step 2 — Assemble the deploy bundle

Create a `deploy/` directory with these four files:

1. **`deploy/Dockerfile`** — copy from `templates/Dockerfile`.
2. **`deploy/.dockerignore`** — copy from `templates/.dockerignore`. This file
   is required: without it, `COPY . .` in the Dockerfile copies `.env` and any
   local credential files into the image layer. Never omit it.
3. **`deploy/requirements.txt`** — list `dlt` and `requests` as a baseline,
   then add any packages the user's `pipeline.py` imports.
4. **`deploy/<platform>.md`** — copy from `templates/deploy/<platform>.md`,
   then substitute the user's cron expression for `CRON_SCHEDULE` and fill in
   any project or account IDs the user has provided.

Secrets (API keys, database URLs, credentials) go into the platform's managed
secret store — Cloud Secret Manager, Azure Key Vault, or AWS Secrets Manager.
They are injected as environment variables at container start. Nothing secret
belongs in the Dockerfile, the image, or any file committed to the repo.

---

## Step 3 — Confirm and summarise

Tell the user:

> Your deploy bundle is ready in `deploy/`.
>
> Next steps (run these yourself):
> 1. Check `deploy/requirements.txt` and add any missing packages.
> 2. Follow `deploy/<platform>.md` to build, push, and schedule the container.
>
> Secrets are injected at runtime via your platform's secret manager — nothing
> sensitive is in the image.
>

---

## Self-check

After producing the bundle, spin up a grader agent with a clean context. Give it
`EVALS.md` and the contents of `deploy/`, and nothing else. Run the eval loop
described in `../../references/running-evals.md`. Fix any `fail` verdicts before
reporting done to the user. On platforms without subagents (e.g. Codex), run the same checklist inline in a fresh reasoning pass instead — see `../../references/running-evals.md`.

For user-facing text in the bundle and instructions, apply the checks in
`../../references/anti-slop.md`: cut filler verbs, hedging openers, and any
sentence that would read identically in a different product's docs.

Platform quirks from past runs are in `MEMORY.md` — check it before writing
platform-specific instructions.
