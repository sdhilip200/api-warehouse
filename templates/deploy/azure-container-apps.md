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

## Step 4 — Create a managed identity and get the Key Vault secret URI

```bash
# Create a managed identity
az identity create \
  --name api-warehouse-identity \
  --resource-group $RESOURCE_GROUP

MANAGED_IDENTITY_ID=$(az identity show \
  --name api-warehouse-identity \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Get the Key Vault secret URI
KEY_VAULT_SECRET_URI=$(az keyvault secret show \
  --vault-name $KV_NAME \
  --name API-KEY \
  --query id -o tsv)

# Assign the managed identity to Key Vault (grant Secret User role)
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee-object-id $(az identity show --name api-warehouse-identity --resource-group $RESOURCE_GROUP --query principalId -o tsv) \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KV_NAME
```

## Step 5 — Create the scheduled Container Apps Job

```bash
CRON_SCHEDULE="0 6 * * *"  # daily 06:00 UTC

az containerapp job create \
  --name api-warehouse-job \
  --resource-group $RESOURCE_GROUP \
  --environment $ENV_NAME \
  --trigger-type Schedule \
  --cron-expression "$CRON_SCHEDULE" \
  --image $IMAGE \
  --registry-server $ACR_NAME.azurecr.io \
  --secrets "api-key=keyvaultref:$KEY_VAULT_SECRET_URI,identityref:$MANAGED_IDENTITY_ID" \
  --env-vars "API_KEY=secretref:api-key"
```

> Tip: Use a managed identity to pull secrets from Key Vault — avoid passing secrets as plain env vars.

## Notes
- Secrets are injected at runtime via Azure Key Vault references — never baked into the image.
- v1 of this bundle is deploy-ready but YOU must run the commands above. Auto-deploy is planned for v2.
