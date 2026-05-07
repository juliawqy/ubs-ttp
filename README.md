# UBS TTP – Bias Mitigation Platform: Setup Guide

> **Project**: Mitigating Unconscious Bias in the Workplace (TTP 2026)
> **Stack**: Next.js · FastAPI · PostgreSQL · AWS EKS · ArgoCD · GitHub Actions · Terraform

---

## Table of Contents

1. [Repo Structure](#1-repo-structure)
2. [Services Overview](#2-services-overview)
3. [Local Development Setup](#3-local-development-setup)
4. [CI/CD Pipeline](#4-cicd-pipeline)
5. [Infrastructure (Terraform)](#5-infrastructure-terraform)
6. [Kubernetes & ArgoCD](#6-kubernetes--argocd)
7. [GitHub Repository Settings](#7-github-repository-settings)
8. [Getting Started Checklist](#8-getting-started-checklist)

---

## 1. Repo Structure

```
ubs-ttp/
├── .github/workflows/          # GitHub Actions CI/CD pipelines
│   ├── ci.yml                  # Runs on every PR: lint, test, build check
│   ├── build-push.yml          # Runs on merge to main: builds & pushes to ECR, updates staging
│   └── deploy-prod.yml         # Runs on version tag (v*.*.*): promotes to production
│
├── frontend/                   # Next.js 14 (TypeScript, Tailwind, React Query)
│   ├── src/app/                # App Router pages (Hiring, Training, Performance, Dashboard)
│   ├── src/components/         # UI components grouped by domain
│   ├── src/lib/api/            # Typed API client (axios wrappers per service)
│   ├── tests/e2e/              # Playwright end-to-end tests
│   └── Dockerfile
│
├── services/                   # Python FastAPI microservices
│   ├── api-gateway/            # Auth (Cognito JWT validation), routing, rate limiting
│   ├── recruitment/            # Use Case 1: Job postings, PII redaction, interviews, panel
│   ├── training/               # Use Case 2: Training modules, IAT, career mapping
│   ├── performance/            # Use Case 3: Performance reviews, bias detection
│   ├── ai-assistant/           # Personalised Assistant (AWS Bedrock + OpenAI)
│   └── analytics/              # Dashboard KPIs, diversity metrics, aggregation
│
├── infrastructure/             # Terraform IaC
│   ├── modules/                # Reusable modules (eks, rds, s3, cognito, sqs-sns, etc.)
│   └── environments/           # Per-environment configs (staging, production)
│
├── k8s/                        # Kubernetes manifests (managed by ArgoCD via Kustomize)
│   ├── base/                   # Shared base: Deployment + Service per microservice
│   └── overlays/               # Environment-specific patches (replica count, image tags)
│       ├── staging/
│       └── production/
│
├── argocd/                     # ArgoCD Application manifests (app-of-apps pattern)
├── scripts/                    # Developer utilities (setup, seed DB, run migrations)
├── docker-compose.yml          # Full local dev stack (all services + Postgres + Redis + LocalStack)
├── docker-compose.test.yml     # Isolated test environment
├── .env.example                # All required environment variable keys
├── Makefile                    # Shortcuts: make dev, make test, make lint
└── .pre-commit-config.yaml     # Pre-commit hooks (ruff, terraform fmt, secret detection)
```

---

## 2. Services Overview

| Service | Port (local) | Responsibility |
|---|---|---|
| `api-gateway` | 8000 | JWT auth via Cognito, request routing, rate limiting |
| `recruitment` | 8001 | Job postings, PII redaction (NER), skills assessment, interview panel assignment |
| `training` | 8002 | Adaptive training module recommendations, IAT (private sandbox), career mapping |
| `performance` | 8003 | Performance review rubrics, AI bias detection in feedback, employee surveys |
| `ai-assistant` | 8004 | Personalised Assistant, bias classifier, Bedrock/OpenAI integration |
| `analytics` | 8005 | Dashboard KPI aggregation: sourcing diversity ratio, promotion velocity, eNPS, etc. |
| `frontend` | 3000 | Next.js dashboard (Hiring tab, Training tab, Performance tab) |

All services expose a `/health` endpoint. Inter-service communication uses **AWS SQS** for async tasks (e.g. bias analysis jobs) and direct HTTP for synchronous calls routed via the api-gateway.

---

## 3. Local Development Setup

### Prerequisites

Install these before starting:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Compose)
- [Node.js 20+](https://nodejs.org/)
- [Python 3.12+](https://www.python.org/)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [Terraform 1.8+](https://developer.hashicorp.com/terraform/install) *(for infra work)*
- [kubectl](https://kubernetes.io/docs/tasks/tools/) + [Helm](https://helm.sh/docs/intro/install/) *(for k8s work)*

### First-time setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_ORG/ubs-ttp.git
cd ubs-ttp

# 2. Run the setup script (copies .env, installs pre-commit + frontend deps)
./scripts/setup-local.sh

# 3. Fill in your API keys in .env
#    Required: OPENAI_API_KEY (or use Bedrock only)
#    Everything else has working LocalStack/local defaults

# 4. Start all services
make dev
```

The `make dev` command starts the full stack via docker-compose:
- PostgreSQL on port 5432
- Redis on port 6379
- LocalStack (S3, SQS, SNS, Textract emulation) on port 4566
- All 6 FastAPI services on ports 8000–8005
- Next.js frontend on port 3000

### Daily workflow

```bash
make dev           # start everything
make test          # run all unit tests
make test-e2e      # run Playwright e2e tests
make lint          # run ruff + eslint
```

### Working on a single service

```bash
# Start only the dependencies + one service
docker compose up postgres redis localstack recruitment

# Or run directly (faster iteration)
cd services/recruitment
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Database migrations

Each service manages its own schema with **Alembic**:

```bash
# Run all migrations
./scripts/run-migrations.sh

# Or per-service
cd services/recruitment
alembic revision --autogenerate -m "add candidates table"
alembic upgrade head
```

---

## 4. CI/CD Pipeline

The pipeline has three stages, each triggered by a different Git event.

### Stage 1 — CI (`ci.yml`) · triggered on every PR to `main` or `develop`

Uses `dorny/paths-filter` to detect which services changed, then runs only the relevant jobs:

1. **Lint** — `ruff check` for Python, `next lint` + `tsc --noEmit` for frontend
2. **Unit tests** — `pytest` with coverage upload to Codecov
3. **Docker build check** — builds each changed service's image (no push) to catch Dockerfile issues early
4. **Terraform validate** — `fmt -check` + `validate` if `infrastructure/` changed
5. **E2e tests** — spins up `docker-compose.test.yml` and runs Playwright (runs after unit tests pass)

All jobs must pass for a PR to be mergeable. Configure this in GitHub branch protection rules (see Section 7).

### Stage 2 — Build & Push (`build-push.yml`) · triggered on push to `main`

Runs after a PR is merged:

1. Authenticates to AWS ECR using **OIDC** (no long-lived AWS keys stored in GitHub)
2. Builds and pushes each service image tagged with the commit SHA and `latest`
3. Updates `k8s/overlays/staging/<service>/kustomization.yaml` with the new image tag
4. Commits and pushes the manifest change back to the repo
5. **ArgoCD detects the manifest change and automatically deploys to staging**
6. For the frontend: runs `next build`, syncs the static output to S3, and invalidates CloudFront

### Stage 3 — Production Deploy (`deploy-prod.yml`) · triggered on a version tag `v*.*.*`

```bash
# To release to production:
git tag v1.0.0
git push origin v1.0.0
```

This retags the ECR image for each service with the version number and updates `k8s/overlays/production/` manifests. ArgoCD is configured with **manual sync** for production — a team member approves the sync in the ArgoCD UI before it goes live.

### Flow diagram

```
Developer opens PR
        │
        ▼
  ci.yml runs
  lint → test → docker build check → terraform validate → e2e
        │ (all pass)
        ▼
  PR merged to main
        │
        ▼
  build-push.yml runs
  build images → push to ECR → update staging k8s manifests → commit
        │
        ▼
  ArgoCD detects manifest change
  → auto-syncs to EKS staging namespace
        │
        ▼ (manual: git tag vX.Y.Z)
  deploy-prod.yml runs
  retag images → update production manifests → commit
        │
        ▼
  ArgoCD awaits manual approval
  → team member clicks Sync in ArgoCD UI
  → deploys to EKS production namespace
```

---

## 5. Infrastructure (Terraform)

All AWS resources are defined in `infrastructure/`. The state is stored remotely in S3 with a DynamoDB lock table — provision these once manually before running Terraform for the first time.

### Bootstrap remote state (one-time)

```bash
# Create the S3 bucket and DynamoDB table for Terraform state
aws s3api create-bucket \
  --bucket ubs-ttp-tfstate-staging \
  --region ap-southeast-1 \
  --create-bucket-configuration LocationConstraint=ap-southeast-1

aws dynamodb create-table \
  --table-name ubs-ttp-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

### Deploy staging infrastructure

```bash
cd infrastructure/environments/staging
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Terraform modules

| Module | What it provisions |
|---|---|
| `networking` | VPC, public/private subnets across 3 AZs, NAT gateway, security groups, ALB |
| `eks` | EKS cluster + managed node groups, IAM OIDC provider for GitHub Actions |
| `rds` | PostgreSQL 16 RDS with primary + read replica across AZs, encrypted with KMS |
| `s3` | Buckets: raw resumes (encrypted, private), redacted resumes, static frontend assets |
| `cognito` | User Pool with MFA required, App Client for the frontend, identity pool |
| `sqs-sns` | SQS queues (bias-analysis, notifications), SNS topics, DLQs |
| `elasticache` | Redis cluster for session caching and rate limiting |
| `cloudfront` | CDN distribution pointing to S3 frontend bucket |
| `ecr` | One ECR repository per microservice, with lifecycle policies |
| `waf` | WAF Web ACL with AWS managed rules, rate limiting |
| `kms` | Customer-managed keys for RDS, S3, and SQS encryption |

---

## 6. Kubernetes & ArgoCD

### Kustomize structure

`k8s/base/` contains the canonical Deployment and Service for each microservice. `k8s/overlays/staging/` and `k8s/overlays/production/` patch those bases with environment-specific values (replica count, image tags, namespace).

The CI pipeline only ever writes to the `newTag` field in the overlay `kustomization.yaml`. Everything else (resource limits, health probes, env secrets) lives in the base and is version-controlled.

### Installing ArgoCD on EKS (one-time)

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Expose the UI (or use port-forward for local access)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get the initial admin password
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d

# Bootstrap the app-of-apps (registers all service Applications at once)
kubectl apply -f argocd/app-of-apps.yaml
```

After bootstrapping, ArgoCD will find all the Application manifests in `argocd/apps/` and start managing each service. Staging auto-syncs; production requires manual approval.

### Namespaces

- `ubs-ttp-staging` — auto-created by ArgoCD via `CreateNamespace=true`
- `ubs-ttp-production` — same
- `argocd` — ArgoCD itself

### Secrets management

Secrets (DB passwords, API keys) are **not** stored in Git. Use **AWS Secrets Manager** and the [External Secrets Operator](https://external-secrets.io/) to sync them into Kubernetes Secrets at deploy time. Each service's Deployment references a `<service>-secrets` Secret via `envFrom`.

---

## 7. GitHub Repository Settings

### Secrets to add (Settings → Secrets → Actions)

| Secret | Description |
|---|---|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `AWS_ROLE_ARN` | IAM role ARN for GitHub Actions OIDC (no static keys needed) |
| `S3_FRONTEND_BUCKET` | S3 bucket name for the Next.js static build |
| `CF_DISTRIBUTION_ID` | CloudFront distribution ID for cache invalidation |

### IAM OIDC setup for GitHub Actions (one-time)

```bash
# Add GitHub as an OIDC identity provider in IAM, then create a role with:
# Trust policy condition:
#   token.actions.githubusercontent.com:sub = repo:YOUR_ORG/ubs-ttp:ref:refs/heads/main
# Permissions: AmazonEC2ContainerRegistryFullAccess, AmazonS3FullAccess, CloudFrontFullAccess
```

### Branch protection rules (Settings → Branches → main)

- Require a pull request before merging
- Require status checks to pass: `lint-and-test-python`, `lint-and-test-frontend`, `e2e`, `docker-build-check`
- Require branches to be up to date before merging
- Do not allow bypassing the above settings

### Recommended branch strategy

```
main          ← production-ready, protected
develop       ← integration branch, auto-deploys to staging
feature/*     ← individual feature branches, PRs go to develop
hotfix/*      ← urgent fixes, PRs go directly to main
```

---

## 8. Getting Started Checklist

Work through these in order when starting the project.

**Day 1 — Local environment**
- [ ] Clone the repo and run `./scripts/setup-local.sh`
- [ ] Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`
- [ ] Run `make dev` and verify all service `/health` endpoints respond
- [ ] Open `http://localhost:3000` and confirm the frontend loads

**Week 1 — Core scaffolding**
- [ ] Set up the GitHub repo with branch protection rules (Section 7)
- [ ] Add the four GitHub Actions secrets
- [ ] Create the IAM OIDC role for GitHub Actions
- [ ] Run `terraform init` and `terraform plan` for staging (don't apply yet — review costs)
- [ ] Add Alembic to each service and create the initial migration for your first table

**Week 2 — First feature**
- [ ] Pick one use case to implement first (recommended: recruitment service → job posting flow)
- [ ] Open a feature branch, make a PR, and watch the CI pipeline run end-to-end
- [ ] Merge to `main`, verify the image is pushed to ECR and staging manifest is updated

**Before going to AWS**
- [ ] Apply staging Terraform to provision EKS, RDS, S3, Cognito, SQS
- [ ] Bootstrap ArgoCD on the EKS cluster
- [ ] Apply `argocd/app-of-apps.yaml` and confirm services sync to staging namespace
- [ ] Run a load test against staging before touching production infrastructure

---

## Key Design Decisions

**Why EKS over ECS?** ArgoCD is a Kubernetes-native GitOps tool. Running it on EKS gives you full ArgoCD compatibility, Kustomize overlays, and a clear path to Helm charts or service meshes (e.g. Istio) as the platform scales.

**Why a monorepo?** All six backend services share domain models, auth patterns, and CI configuration. A monorepo means one PR can atomically update the API contract and the frontend component that consumes it, avoiding cross-repo version drift.

**Why LocalStack for local dev?** It emulates S3, SQS, SNS, and Textract locally so every developer can run the full stack without needing AWS credentials or incurring costs. The `AWS_ENDPOINT_URL` env var switches the boto3 client between LocalStack and real AWS.

**Why OIDC for GitHub Actions?** Eliminates long-lived AWS access keys stored as GitHub secrets — a common source of credential leaks. GitHub Actions exchanges a short-lived OIDC token for a scoped AWS role session at runtime.
