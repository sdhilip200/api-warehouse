---
name: schedule
description: >
  Use this skill when the user wants to schedule the pipeline, deploy the pipeline
  on a cron, run the pipeline automatically, set up a recurring pipeline run, or
  containerize and deploy the data pipeline to the cloud.
  Trigger phrases include: "schedule the pipeline", "deploy the pipeline",
  "run on a cron", "run every day", "automate the pipeline", "containerize and deploy",
  or any request to run the landed pipeline on a recurring schedule in the cloud.
---

# Schedule Skill

## What this skill does (v1)

This skill produces a **deploy-ready bundle** — a `Dockerfile`, a starter `requirements.txt`,
and copy-paste deployment instructions for your chosen cloud platform.

**v1 does NOT auto-deploy to your cloud.** You run the commands yourself.
Auto-deploy is planned for v2.

---

## Step 1 — Ask the user which platform

Ask:

> Which cloud platform would you like to deploy to?
> 1. Google Cloud Run (Cloud Run Job + Cloud Scheduler)
> 2. Azure Container Apps (Job with cron trigger)
> 3. AWS ECS (Fargate scheduled task + EventBridge)

Also ask:

> What cron schedule would you like? (e.g. `"0 6 * * *"` for 6 AM UTC daily)

---

## Step 2 — Create the deploy bundle

Create a `deploy/` directory in the user's project with:

1. **`deploy/Dockerfile`** — copy from `templates/Dockerfile` (in the plugin).
2. **`deploy/requirements.txt`** — a starter file listing the user's pipeline dependencies.
   At minimum include: `dlt`, `requests`. Add any extras the user's `pipeline.py` imports.
3. **`deploy/<platform>.md`** — copy from `templates/deploy/<platform>.md` and fill in:
   - Replace `CRON_SCHEDULE` with the cron expression the user provided.
   - Replace placeholder project/account IDs with the user's values if known.

---

## Step 3 — Confirm and summarise

Tell the user:

> Your deploy bundle is ready in `deploy/`.
>
> **Next steps (run these yourself):**
> 1. Review `deploy/requirements.txt` and add any missing dependencies.
> 2. Follow the instructions in `deploy/<platform>.md` to build, push, and schedule the container.
>
> Secrets are injected at runtime via your cloud platform's secret manager —
> they are never baked into the image.
>
> When you are ready to auto-deploy from Claude Code (v2), run `/schedule` again.

---

## Secrets policy

Secrets (API keys, database URLs, credentials) must **never** be written into the Dockerfile
or the image. The Dockerfile comment and deploy guides both enforce this:
secrets are passed as environment variables at runtime using the platform's managed secret store
(Cloud Secret Manager / Azure Key Vault / AWS Secrets Manager).
