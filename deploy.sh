#!/bin/bash
set -e

echo "🚀 Starting deployment process..."

# 1. Основные переменные окружения
export AWS_REGION=${AWS_REGION:-"us-east-1"}
export PROJECT_NAME=${PROJECT_NAME:-"ecommerce-api"}
export ENVIRONMENT=${ENVIRONMENT:-"prod"}
export CLUSTER_NAME=${CLUSTER_NAME:-"ecommerce-api-eks"}

# Проверка самых важных секретов
if [ -z "$TF_DB_PASSWORD" ] || [ -z "$APP_SECRET_KEY" ]; then
    echo "❌ ОШИБКА: Пожалуйста, задайте переменные окружения TF_DB_PASSWORD и APP_SECRET_KEY."
    echo "Пример: export TF_DB_PASSWORD='my-strong-password' && export APP_SECRET_KEY='my-secret'"
    exit 1
fi

# Секреты Stripe (если не заданы, подставим пустышки для теста)
export STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-"sk_test_replace_me"}
export STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-"whsec_replace_me"}

# 2. Получаем выводы из Terraform
echo "🔍 Чтение инфраструктурных данных из Terraform..."
cd terraform
# Убедимся, что стейт инициализирован
terraform init -backend=false > /dev/null 2>&1 || true
export ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
export RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
cd ..

if [ -z "$ECR_REPO_URL" ] || [ -z "$RDS_ENDPOINT" ] || [ "$ECR_REPO_URL" = "No outputs found" ]; then
    echo "❌ ОШИБКА: Не удалось получить данные из Terraform. Инфраструктура развернута? (Сделай terraform apply в папке terraform)"
    exit 1
fi

# 3. Сборка и отправка образа (Docker)
echo "🐳 Сборка и отправка Docker-образа в AWS ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$(echo "$ECR_REPO_URL" | cut -d'/' -f1)"

# Используем хэш коммита git как тег образа, либо 'latest' если git не настроен
export IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
export IMAGE_URI="${ECR_REPO_URL}:${IMAGE_TAG}"

docker build -t "$IMAGE_URI" .
docker push "$IMAGE_URI"

# 4. Настройка доступа к Kubernetes
echo "☸️  Настройка kubectl для доступа к EKS кластеру..."
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

# 5. Деплой приложения в Kubernetes
echo "📦 Развертывание приложения..."

export DATABASE_URL="postgresql+asyncpg://ecommerce_admin:${TF_DB_PASSWORD}@${RDS_ENDPOINT}:5432/ecommerce"

# Применяем простые манифесты
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml

# Применяем манифесты с подстановкой переменных (Секреты)
echo "   -> Создание секретов..."
envsubst < k8s/secrets.yaml | kubectl apply -f -

# Миграции БД
echo "   -> Запуск миграций базы данных..."
kubectl delete job ecommerce-db-migration -n ecommerce --ignore-not-found
envsubst < k8s/migration-job.yaml | kubectl apply -f -

echo "⏳ Ожидание завершения миграций (макс 2 мин)..."
kubectl wait --for=condition=complete job/ecommerce-db-migration -n ecommerce --timeout=120s

# Само приложение (API) и маршрутизация
echo "   -> Обновление веб-сервера (API)..."
envsubst < k8s/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

echo "✅ Деплой успешно завершен!"
echo "Балансировщик NGINX скоро выдаст внешний адрес. Проверить его можно командой:"
echo "kubectl get ingress -n ecommerce"
