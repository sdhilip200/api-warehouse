# Deploy to Google Cloud Run (Scheduled Job)

## Prerequisites
- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally
- Artifact Registry repository (or Container Registry)

## Step 1 — Build and push the image

```bash
PROJECT_ID=your-gcp-project-id
REGION=us-central1
IMAGE=gcr.io/$PROJECT_ID/api-warehouse-pipeline:latest

# Authenticate Docker to Container Registry
gcloud auth configure-docker gcr.io

docker build -t $IMAGE .
docker push $IMAGE
```

## Step 2 — Store secrets in Secret Manager (never in the image)

```bash
# Example: store your API key
echo -n "your-api-key-value" | gcloud secrets create API_KEY --data-file=-
echo -n "your-db-url" | gcloud secrets create DB_URL --data-file=-
```

Grant the Cloud Run service account access:
```bash
SA=your-run-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud secrets add-iam-policy-binding API_KEY \
  --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```

## Step 3 — Create the Cloud Run Job

```bash
gcloud run jobs create api-warehouse-job \
  --image $IMAGE \
  --region $REGION \
  --set-secrets=API_KEY=API_KEY:latest,DB_URL=DB_URL:latest
```

## Step 4 — Schedule with Cloud Scheduler

Replace `CRON_SCHEDULE` with your desired schedule (e.g. `"0 6 * * *"` for 6 AM daily).

```bash
gcloud scheduler jobs create http api-warehouse-trigger \
  --location $REGION \
  --schedule "CRON_SCHEDULE" \
  --uri "https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/api-warehouse-job:run" \
  --http-method POST \
  --oauth-service-account-email $SA
```

## Notes
- Secrets are injected at runtime by Cloud Run — they are never baked into the image.
- v1 of this bundle is deploy-ready but YOU must run the commands above. Auto-deploy is planned for v2.
