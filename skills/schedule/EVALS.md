# Schedule Skill — Evals

Run these checks using the eval loop in `../../references/running-evals.md`.
Spin up a grader agent with a clean context; give it this file and the `deploy/`
directory contents only.

## Checks

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | `deploy/Dockerfile` exists | File is present in `deploy/` |
| 2 | `deploy/.dockerignore` exists | File is present in `deploy/`; a missing `.dockerignore` means local secrets can leak into the image layer |
| 3 | No secret value baked into image | `Dockerfile` and `requirements.txt` contain no literal API keys, passwords, or connection strings (env-var names are fine; values are not) |
| 4 | Secrets routed through managed secret store | The platform `.md` instructs the user to store secrets in Cloud Secret Manager / Azure Key Vault / AWS Secrets Manager and inject them as env vars at runtime |
| 5 | Scheduled trigger configured | The platform `.md` includes a cron expression and the scheduler resource (Cloud Scheduler job, ACA cron trigger, or EventBridge rule) with the user's schedule substituted for `CRON_SCHEDULE` |
| 6 | v1 no-auto-deploy stated | The output to the user explicitly says v1 does not auto-deploy and that the user runs the commands themselves |
| 7 | Platform `.md` present | A file matching `deploy/gcp.md`, `deploy/azure.md`, or `deploy/aws.md` (matching the chosen platform) exists in `deploy/` | `skipped` if platform was not chosen yet |
