# Deployment Runbook (AWS EKS + RDS)

This runbook assumes you deploy from Linux/macOS shell with these tools installed:
- aws cli
- terraform
- kubectl
- docker

## 1) Set environment variables

```bash
export AWS_REGION=us-east-1
export PROJECT_NAME=ecommerce-api
export ENVIRONMENT=prod
export CLUSTER_NAME=ecommerce-api-eks
export TF_DB_PASSWORD='REPLACE_ME_STRONG_DB_PASSWORD'

# Kubernetes app secrets
export APP_SECRET_KEY='REPLACE_ME_APP_SECRET'
export STRIPE_SECRET_KEY='REPLACE_ME_STRIPE_SECRET'
export STRIPE_WEBHOOK_SECRET='REPLACE_ME_STRIPE_WEBHOOK_SECRET'
```

## 2) Provision/Update infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}" \
  -var="environment=${ENVIRONMENT}" \
  -var="cluster_name=${CLUSTER_NAME}" \
  -var="db_password=${TF_DB_PASSWORD}"
terraform apply \
  -var="aws_region=${AWS_REGION}" \
  -var="project_name=${PROJECT_NAME}" \
  -var="environment=${ENVIRONMENT}" \
  -var="cluster_name=${CLUSTER_NAME}" \
  -var="db_password=${TF_DB_PASSWORD}"
```

Collect outputs:

```bash
export ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
export RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
```

## 3) Build and push Docker image to ECR

```bash
cd ..
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "$(echo "${ECR_REPO_URL}" | cut -d'/' -f1)"

export IMAGE_TAG=$(git rev-parse --short HEAD)
export IMAGE_URI="${ECR_REPO_URL}:${IMAGE_TAG}"

docker build -t "${IMAGE_URI}" .
docker push "${IMAGE_URI}"
```

## 4) Configure kubectl for EKS

```bash
aws eks update-kubeconfig --region "${AWS_REGION}" --name "${CLUSTER_NAME}"
```

## 5) Create namespace and runtime secrets

Apply namespace:

```bash
kubectl apply -f k8s/namespace.yaml
```

Build DB URL used by application:

```bash
export DATABASE_URL="postgresql+asyncpg://ecommerce_admin:${TF_DB_PASSWORD}@${RDS_ENDPOINT}:5432/ecommerce"
```

Create/update app secret (idempotent apply pattern):

```bash
kubectl -n ecommerce create secret generic ecommerce-api-secrets \
  --from-literal=DATABASE_URL="${DATABASE_URL}" \
  --from-literal=SECRET_KEY="${APP_SECRET_KEY}" \
  --from-literal=STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}" \
  --from-literal=STRIPE_WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET}" \
  --dry-run=client -o yaml | kubectl apply -f -
```

## 6) Apply app manifests with your real image/domain

Set your public API domain:

```bash
export API_DOMAIN='api.your-domain.com'
```

Apply manifests using inline substitutions:

```bash
sed "s|your-account-id.dkr.ecr.us-east-1.amazonaws.com/ecommerce-api:latest|${IMAGE_URI}|g" k8s/deployment.yaml | kubectl apply -f -
sed "s|api.your-domain.com|${API_DOMAIN}|g" k8s/ingress.yaml | kubectl apply -f -
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## 7) Verify rollout and health

```bash
kubectl -n ecommerce get pods
kubectl -n ecommerce rollout status deployment/ecommerce-api --timeout=180s
kubectl -n ecommerce get svc,ingress
kubectl -n ecommerce logs deployment/ecommerce-api --tail=100
```

Optional health check via port-forward:

```bash
kubectl -n ecommerce port-forward deployment/ecommerce-api 8000:8000
curl -s http://127.0.0.1:8000/health
```

## 8) Common failure checks

- Pod crashes at startup:
  - Verify `DATABASE_URL` and `SECRET_KEY` in `ecommerce-api-secrets`.
- Migration errors in initContainer:
  - Check `kubectl -n ecommerce logs deploy/ecommerce-api -c migrate-db`.
- No external traffic:
  - Verify ingress controller exists and DNS points to ingress LB.
- Image pull errors:
  - Ensure pushed image tag exists in ECR and cluster nodes can pull from ECR.
