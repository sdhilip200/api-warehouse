# Deploy to AWS ECS (Scheduled Task via EventBridge)

## Prerequisites
- AWS account with appropriate IAM permissions
- `aws` CLI installed and configured
- Docker installed locally
- Amazon ECR repository

## Step 1 — Build and push the image

```bash
AWS_ACCOUNT_ID=123456789012
REGION=us-east-1
REPO=api-warehouse-pipeline
IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO:latest

aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker build -t $IMAGE .
docker push $IMAGE
```

## Step 2 — Store secrets in AWS Secrets Manager (never in the image)

```bash
aws secretsmanager create-secret \
  --name api-warehouse/API_KEY \
  --secret-string "your-api-key-value"

aws secretsmanager create-secret \
  --name api-warehouse/DB_URL \
  --secret-string "your-db-url"
```

## Step 3 — Register an ECS Task Definition

Create `task-definition.json` referencing your image and secrets:

```json
{
  "family": "api-warehouse-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "pipeline",
      "image": "IMAGE_URI",
      "secrets": [
        {"name": "API_KEY", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:api-warehouse/API_KEY"},
        {"name": "DB_URL",  "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:api-warehouse/DB_URL"}
      ]
    }
  ]
}
```

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

## Step 4 — Schedule with EventBridge

```bash
CLUSTER=my-ecs-cluster
SUBNET_ID=subnet-xxxxxxxx
SG_ID=sg-xxxxxxxx
TASK_ROLE_ARN=arn:aws:iam::ACCOUNT:role/ecsTaskRole
CRON_SCHEDULE="cron(0 6 * * ? *)"  # daily 06:00 UTC — EventBridge cron syntax

aws events put-rule \
  --name api-warehouse-schedule \
  --schedule-expression "$CRON_SCHEDULE" \
  --state ENABLED

aws events put-targets \
  --rule api-warehouse-schedule \
  --targets "[{
    \"Id\": \"api-warehouse-ecs\",
    \"Arn\": \"arn:aws:ecs:$REGION:$AWS_ACCOUNT_ID:cluster/$CLUSTER\",
    \"RoleArn\": \"$TASK_ROLE_ARN\",
    \"EcsParameters\": {
      \"TaskDefinitionArn\": \"arn:aws:ecs:$REGION:$AWS_ACCOUNT_ID:task-definition/api-warehouse-task\",
      \"LaunchType\": \"FARGATE\",
      \"NetworkConfiguration\": {
        \"awsvpcConfiguration\": {
          \"Subnets\": [\"$SUBNET_ID\"],
          \"SecurityGroups\": [\"$SG_ID\"],
          \"AssignPublicIp\": \"ENABLED\"
        }
      }
    }
  }]"
```

## Notes
- Secrets are injected at runtime by ECS from Secrets Manager — never baked into the image.
- v1 of this bundle is deploy-ready but YOU must run the commands above. Auto-deploy is planned for v2.
