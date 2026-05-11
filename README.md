# UBS TTP — Bias Mitigation Platform

A platform to help managers identify and address unconscious bias in hiring, promotion, and team dynamics.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Node.js + Express, plain HTML/CSS/JS |
| Backend | Python 3.12 + FastAPI (microservices) |
| Database | PostgreSQL 16 |
| Document storage | AWS S3 |
| Async jobs | AWS SQS |
| AI | Anthropic Claude API (controlled, cost-capped) |
| Document parsing | pdfplumber (no AI cost) |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

## Services

| Service | Port | Responsibility |
|---|---|---|
| `recruitment` | 8001 | Job postings, blind profiles, interviews, panel |
| `training` | 8002 | Training modules, IAT sandbox, career mapping |
| `performance` | 8003 | Performance reviews, bias detection, feedback |
| `ai-assistant` | 8004 | Personalised assistant (Claude API) |
| `analytics` | 8005 | Dashboard KPIs and diversity metrics |
| `frontend` | 3000 | Manager dashboard UI |
| `shared` | — | Reusable library: bias_analyzer, document_parser, ai_client, notification |

## Quick start

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
make dev
```

Open http://localhost:3000

## Development workflow

```bash
make dev          # start full stack
make test         # run all pytest tests
make lint         # ruff + JS syntax check
make security     # bandit + safety CVE scan
make docs         # generate HTML docs from source
```

## Key principles

- **TDD** — write tests before implementation, every feature
- **SOLID** — especially SRP; go granular, one class one job
- **API-first** — external vendor features called via adapter interfaces
- **Shared modules** — no duplicate logic across services; reuse via `services/shared/`
- **AI as last resort** — use traditional methods first; AI only when necessary

## Project plan

See [PLAN.md](./PLAN.md) for the full 8-week roadmap and stretch goals.
