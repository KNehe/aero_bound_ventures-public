<p align="center">
  <img src="frontend/public/logo.png" alt="Aero Bound Ventures logo" width="120" />
</p>

<h1 align="center">Aero Bound Ventures</h1>

<p align="center">
  A full-stack flight booking platform built with Next.js, FastAPI, PostgreSQL,
  Redis, and Kafka.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-000000?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Kafka-231F20?logo=apachekafka&logoColor=white" alt="Kafka" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes" />
</p>

## Overview

Aero Bound Ventures integrates flight search, booking, payments, authentication,
notifications, and administration in one application. The backend can use the
Amadeus API for live flight data or local fixtures for development and demos.

## Core Capabilities

- Search, price, book, and cancel flights
- Select seats and manage bookings
- Process Pesapal payments and refunds
- Authenticate with credentials or Google OAuth
- Deliver email and real-time notifications through Kafka and Redis
- Manage bookings, revenue, permissions, and uploaded tickets

## Architecture

```text
Next.js frontend
       |
       | REST and SSE
       v
FastAPI API ---- PostgreSQL
    |   |
    |   +------ Redis cache and Pub/Sub
    |
    +---------- Kafka ---- notification worker
    |
    +---------- Amadeus, Pesapal, Cloudinary, Google OAuth, SMTP
```

## Technology

| Area | Main tools |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Zustand, TanStack Query |
| Backend | FastAPI, Python, SQLModel, Alembic, uv |
| Data and events | PostgreSQL, Redis, Kafka |
| Infrastructure | Docker Compose, Helm, Kubernetes, Terraform, AWS |
| Delivery and configuration | GitHub Actions, Doppler |

## Repository Layout

```text
backend/      FastAPI API, worker, migrations, tests, and Docker Compose
frontend/     Next.js application
helm/         Backend and DopplerSecret Helm charts
terraform/    EC2 production and EKS staging infrastructure
scripts/      Local Kubernetes bootstrap automation
```

## Local Development

### Backend

Prerequisites: Docker, Docker Compose, and an authenticated
[Doppler CLI](https://docs.doppler.com/docs/install-cli).

```bash
cd backend
doppler setup
export DOPPLER_TOKEN="$(doppler configs tokens create docker --max-age 15m --plain)"
docker compose up -d --wait db redis kafka
docker compose build fastapi-app
docker compose run --rm migrate
docker compose up -d fastapi-app notification-worker
```

The API is available at `http://localhost:8000`; its Swagger documentation is
at `http://localhost:8000/docs`.

See [backend/README.md](backend/README.md) for configuration, migrations,
management commands, observability services, and Kubernetes development.

### Frontend

Prerequisite: Node.js 20 or later.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The frontend is available at `http://localhost:3000`. Set
`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `.env.local`.

## Verification

```bash
cd backend
uv run pytest
cd ../frontend
npm run lint
```

For infrastructure changes:

```bash
terraform -chdir=terraform validate
terraform -chdir=terraform plan
```

## Deployment

Docker Compose on EC2 remains the production deployment path. EKS is an
independent, production-like staging environment managed with Terraform, Helm,
GitHub Actions, and the Doppler Kubernetes Operator.

## License

MIT
