# E-Commerce API

A production-grade RESTful e-commerce API built with FastAPI and PostgreSQL. Features JWT authentication, Stripe payment integration, Kubernetes deployment on AWS EKS, and a full observability stack with Prometheus, Grafana, Loki, and Promtail.

---

## Tech Stack

| Category | Technology |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL, Alembic migrations |
| **Auth** | JWT (JSON Web Tokens) |
| **Payments** | Stripe API |
| **Containerization** | Docker, Docker Compose, Nginx |
| **Orchestration** | Kubernetes (AWS EKS) |
| **Infrastructure** | Terraform (AWS VPC, EKS, RDS, ECR) |
| **CI/CD** | GitHub Actions |
| **Observability** | Prometheus, Grafana, Loki, Promtail |

---

## Features

- JWT-based authentication with admin roles
- Product catalog with search and category filtering
- Shopping cart management per user
- Stripe Payment Intent checkout and webhook handling
- Order history per user
- User address management
- Transactional email notifications
- Metrics and log monitoring out of the box

---

## Project Structure

```
ecommerce-api/
├── app/
│   ├── api/
│   │   ├── dependencies.py        # JWT auth dependencies
│   │   └── endpoints/
│   │       ├── auth.py            # Register, login
│   │       ├── products.py        # Product CRUD
│   │       ├── cart.py            # Cart management
│   │       ├── payments.py        # Stripe checkout & webhooks
│   │       └── users.py           # User profile & addresses
│   ├── core/
│   │   ├── config.py              # Settings via pydantic-settings
│   │   └── security.py            # JWT & password hashing
│   ├── db/
│   │   └── database.py            # Async SQLAlchemy engine
│   ├── models/                    # SQLAlchemy ORM models
│   ├── schemas/                   # Pydantic request/response schemas
│   └── services/
│       └── email.py               # Email service
├── alembic/                       # Database migrations
├── k8s/                           # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml
│   └── migration-job.yaml
├── terraform/                     # AWS infrastructure as code
│   ├── vpc.tf
│   ├── eks.tf
│   ├── rds.tf
│   └── main.tf
├── monitoring/                    # Observability stack configs
│   ├── prometheus.yml
│   ├── loki.yml
│   ├── promtail.yml
│   └── grafana/
├── tests/                         # pytest test suite
├── nginx/nginx.conf
├── Dockerfile
└── docker-compose.yaml
```

---

## Quick Start (Local)

### Prerequisites

- Docker and Docker Compose
- Python 3.14+
- uv package manager

### 1. Clone the repository

```bash
git clone https://github.com/dimashabdyken/ecommerce-api.git
cd ecommerce-api
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/ecommerce
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Start the stack

```bash
docker compose up -d
```

### 4. Run database migrations

```bash
docker compose exec app alembic upgrade head
```

### 5. Access the services

- API docs (Swagger): http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin / admin)

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and receive JWT token |

### Products

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/products` | List products with search and filter | Public |
| GET | `/products/{id}` | Get product by ID | Public |
| POST | `/products` | Create product | Admin |
| PUT | `/products/{id}` | Update product | Admin |
| DELETE | `/products/{id}` | Delete product | Admin |

### Cart

| Method | Endpoint | Description |
|---|---|---|
| GET | `/cart` | View current user cart |
| POST | `/cart/items` | Add item to cart |
| PUT | `/cart/items/{id}` | Update item quantity |
| DELETE | `/cart/items/{id}` | Remove item |
| DELETE | `/cart` | Clear entire cart |

### Payments

| Method | Endpoint | Description |
|---|---|---|
| POST | `/payments/checkout` | Create Stripe Payment Intent |
| POST | `/payments/webhook` | Stripe webhook handler |
| GET | `/payments/orders` | View order history |

---

## Authentication

The API uses JWT Bearer tokens. To authenticate in Swagger UI:

1. Register via `POST /auth/register` or login via `POST /auth/login`
2. Copy the `access_token` from the response
3. Click Authorize in Swagger UI and enter `Bearer <your_token>`

---

## Running Tests

```bash
uv sync
uv run pytest tests/ -v
uv run pytest tests/ --cov=app --cov-report=term-missing
```

Test coverage includes auth, products, cart, payments, and users.

---

## Observability

The monitoring stack runs via Docker Compose and is fully auto-provisioned:

- Prometheus scrapes the `/metrics` endpoint from FastAPI
- Grafana dashboard shows request rate, p95 response time, and error rate
- Loki stores and indexes logs from all containers
- Promtail collects logs from FastAPI and Nginx

No manual setup needed — everything starts with `docker compose up`.

---

## AWS Deployment

### Prerequisites

- AWS CLI configured with IAM user credentials
- Terraform installed
- kubectl installed

### 1. Provision infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Creates VPC, EKS cluster, RDS PostgreSQL instance, and ECR registry.

### 2. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name ecommerce-api
```

### 3. Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

### 4. Tear down

```bash
terraform destroy
```

---

## CI/CD Pipeline

GitHub Actions runs on every push to `main` and on pull requests:

1. Lint with ruff
2. Run pytest with a PostgreSQL service container
3. Build Docker image

---

