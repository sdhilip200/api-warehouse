# Schedule Skill — Memory

Platform-specific deploy quirks collected from past runs. Add an entry when a
platform behaves differently than the template assumes; one line per entry is enough.

## Entries

- **GCP Cloud Run Jobs**: `gcloud run jobs execute` is a one-off trigger; the
  recurring schedule lives in Cloud Scheduler, which calls
  `gcloud run jobs execute --region=REGION JOB_NAME`. Remind the user both
  resources (the job and the scheduler) must be created.
