# Deploy to Azure Container Apps (Scheduled Job)

## Prerequisites
- Azure subscription
- `az` CLI installed and authenticated
- Docker installed locally
- Azure Container Registry (ACR)

## Step 1 — Build and push the image

```bash
RESOURCE_GROUP=my-resource-group
ACR_NAME=myacr
IMAGE=$ACR_NAME.azurecr.io/api-warehouse-pipeline:latest

az acr login --name $ACR_NAME
docker build -t $IMAGE .
docker push $IMAGE
```

## Step 2 — Store secrets in Azure Key Vault (never in the image)

```bash
KV_NAME=my-keyvault

az keyvault secret set --vault-name $KV_NAME --name API-KEY --value "your-api-key-value"
az keyvault secret set --vault-name $KV_NAME --name DB-URL --value "your-db-url"
```

## Step 3 — Create the Container Apps Environment

```bash
LOCATION=eastus
ENV_NAME=api-warehouse-env

az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 4 — Create the scheduled Container Apps Job

Replace `CRON_SCHEDULE` with your desired cron expression (e.g. `"0 6 * * *"` for 6 AM daily).

```bash
az containerapp job create \
  --name api-warehouse-job \
  --resource-group $RESOURCE_GROUP \
  --environment $ENV_NAME \
  --trigger-type Schedule \
  --cron-expression "CRON_SCHEDULE" \
  --image $IMAGE \
  --registry-server $ACR_NAME.azurecr.io \
  --secrets "api-key=keyvaultref:<KEY_VAULT_SECRET_URI>,identityref:<MANAGED_IDENTITY_ID>" \
  --env-vars "API_KEY=secretref:api-key"
```

> Tip: Use a managed identity to pull secrets from Key Vault — avoid passing secrets as plain env vars.

## Notes
- Secrets are injected at runtime via Azure Key Vault references — never baked into the image.
- v1 of this bundle is deploy-ready but YOU must run the commands above. Auto-deploy is planned for v2.
