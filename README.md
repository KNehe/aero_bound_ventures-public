<p align="center">
  <img src="frontend/public/logo.png" alt="Aero Bound Ventures Logo" width="120" />
</p>

<h1 align="center">Aero Bound Ventures</h1>

<p align="center">
  A full-stack flight booking platform with real-time search, seat selection, integrated payments, and an admin dashboard — deployed on AWS via CI/CD.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js_15-000000?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Kafka-231F20?logo=apachekafka&logoColor=white" alt="Kafka" />
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white" alt="Terraform" />
  <img src="https://img.shields.io/badge/AWS_EC2-FF9900?logo=amazonec2&logoColor=white" alt="AWS" />
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Management Commands](#management-commands)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Event-Driven Architecture](#event-driven-architecture)
- [Observability](#observability)
- [CI/CD & Deployment](#cicd--deployment)
- [Testing & Code Quality](#testing--code-quality)
- [License](#license)

---

## Overview

Aero Bound Ventures is a production-grade flight booking application that integrates with the **Amadeus Flight API** for real-time flight data and the **Pesapal Payment Gateway** for secure USD transactions. It features an event-driven notification pipeline, group-based admin permissions, and full observability through Prometheus, Grafana, and Loki.

---

## Key Features

| Area | Highlights |
|---|---|
| **Flight Search** | Real-time search across multiple airlines via the Amadeus API (one-way & round-trip) |
| **Price Confirmation** | Verify live pricing before booking to prevent stale-offer errors |
| **Seat Maps** | Visual seat selection for booked flights |
| **Booking Management** | Create, view, and cancel flight bookings with PNR tracking |
| **Payments** | Pesapal iframe modal integration (USD only), IPN webhooks, refund support |
| **Auth** | JWT-based authentication with HTTP-only cookies, Google OAuth 2.0 login, password reset flow |
| **Admin Dashboard** | Booking stats, revenue tracking, booking management, and ticket upload (Cloudinary) |
| **Notifications** | Real-time via SSE (Redis Pub/Sub), with event-driven email notifications via Kafka consumers |
| **Pagination** | Cursor-based pagination for bookings, notifications, and admin views |
| **Observability** | Prometheus metrics, Grafana dashboards, Loki + Promtail for centralized logging |

---

## Architecture

```
┌──────────────────┐       ┌──────────────────────────────────────────────────────┐
│   Next.js 15     │       │  FastAPI Backend                                    │
│   (React 19)     │ ◄──── │  ┌────────┐  ┌────────┐  ┌─────────┐  ┌──────────┐│
│                  │  REST  │  │ Routers│──│  CRUD  │──│ Models  │──│PostgreSQL││
│  Zustand Store   │  SSE   │  └───┬────┘  └────────┘  └─────────┘  └──────────┘│
│  TanStack Query  │       │      │                                              │
└──────────────────┘       │  ┌───▼────────────────┐  ┌────────────┐             │
                           │  │ External Services  │  │   Redis    │             │
                           │  │ ├─ Amadeus Flight  │  │ (Caching + │             │
                           │  │ ├─ Pesapal Payment │  │  Pub/Sub)  │             │
                           │  │ ├─ Cloudinary CDN  │  └────────────┘             │
                           │  │ └─ Email (SMTP)    │                             │
                           │  └────────────────────┘  ┌────────────┐             │
                           │                          │   Kafka    │             │
                           │  ┌────────────────────┐  │ (Event Bus)│             │
                           │  │ Kafka Consumers    │◄─┤            │             │
                           │  │ ├─ User Events     │  └────────────┘             │
                           │  │ ├─ Booking Events  │                             │
                           │  │ ├─ Payment Events  │  ┌────────────┐             │
                           │  │ └─ Ticket Events   │  │Observability             │
                           │  └────────────────────┘  │ Prometheus │             │
                           │                          │ Grafana    │             │
                           │                          │ Loki       │             │
                           │                          └────────────┘             │
                           └──────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| [Next.js 15](https://nextjs.org/) (React 19) | Framework with Turbopack dev server |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Tailwind CSS 4](https://tailwindcss.com/) | Utility-first styling |
| [Zustand](https://zustand-demo.pmnd.rs/) | Client-side state management |
| [TanStack Query](https://tanstack.com/query) | Server state management & caching |
| [NProgress](https://ricostacruz.com/nprogress/) | Navigation progress indicator |
| [React Icons](https://react-icons.github.io/react-icons/) | Icon library |

### Backend

| Technology | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Async Python web framework |
| [Python 3.12+](https://www.python.org/) | Runtime |
| [SQLModel](https://sqlmodel.tiangolo.com/) | ORM (SQLAlchemy + Pydantic) |
| [PostgreSQL 16](https://www.postgresql.org/) | Relational database |
| [Redis](https://redis.io/) | Caching, Pub/Sub for SSE notifications |
| [Confluent Kafka](https://www.confluent.io/) | Event-driven message broker |
| [Alembic](https://alembic.sqlalchemy.org/) | Database migrations |
| [Typer](https://typer.tiangolo.com/) | CLI management commands |
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager |

### External Services

| Service | Purpose |
|---|---|
| [Amadeus API](https://developers.amadeus.com/) | Flight search, pricing, booking, seat maps, cancellation |
| [Pesapal](https://developer.pesapal.com/) | Payment gateway (USD only) — IPN, refunds |
| [Cloudinary](https://cloudinary.com/) | Ticket file uploads & CDN |
| [Google OAuth 2.0](https://developers.google.com/identity) | Social login |
| SMTP (Gmail) | Transactional email notifications |

### Infrastructure & DevOps

| Technology | Purpose |
|---|---|
| [Docker](https://www.docker.com/) | Multi-stage builds & containerization |
| [Docker Compose](https://docs.docker.com/compose/) | Multi-service orchestration |
| [Terraform](https://www.terraform.io/) | AWS infrastructure as code |
| [GitHub Actions](https://github.com/features/actions) | CI/CD — plan, apply, deploy |
| [Nginx](https://nginx.org/) | Reverse proxy with SSL (Certbot) |
| [AWS EC2](https://aws.amazon.com/ec2/) | Application hosting |

### Observability

| Technology | Purpose |
|---|---|
| [Prometheus](https://prometheus.io/) | Metrics collection |
| [Grafana](https://grafana.com/) | Dashboards & alerting |
| [Loki](https://grafana.com/oss/loki/) | Log aggregation |
| [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/) | Log shipping agent |

---

## Project Structure

```
aero_bound_ventures/
├── backend/                    # FastAPI REST API
│   ├── main.py                 # App entry point, lifespan events, middleware
│   ├── manage.py               # CLI commands (create-super-user, create-admin)
│   ├── routers/                # API route handlers
│   │   ├── flights.py          # Flight search, booking, cancellation, seat maps
│   │   ├── payments.py         # Pesapal payment initiation, callbacks, IPN, refunds
│   │   ├── users.py            # Registration, login, logout, password reset
│   │   ├── oauth.py            # Google OAuth2 flow
│   │   ├── admin.py            # Admin dashboard (stats, bookings)
│   │   ├── tickets.py          # Ticket upload (Cloudinary)
│   │   ├── notifications.py    # SSE streams, CRUD for notifications
│   │   └── health.py           # System health check (DB, Redis, Kafka)
│   ├── models/                 # SQLModel database models
│   │   ├── users.py            # User model (supports local + Google auth)
│   │   ├── bookings.py         # Booking model with status enum
│   │   ├── permissions.py      # Group, Permission, UserGroup, UserPermission
│   │   ├── notifications.py    # Notification model with type enum
│   │   └── constants.py        # Admin group & permission definitions
│   ├── schemas/                # Pydantic request/response schemas
│   ├── crud/                   # Database access layer
│   ├── external_services/      # Third-party API integrations
│   │   ├── flight.py           # Amadeus SDK wrapper
│   │   ├── pesapal.py          # Pesapal REST client
│   │   ├── cloudinary_service.py # File upload service
│   │   ├── email.py            # SMTP email sender
│   │   └── cache.py            # Redis caching utilities
│   ├── consumers/              # Kafka event consumers
│   │   ├── user_notifications.py
│   │   ├── booking_notifications.py
│   │   ├── payment_notifications.py
│   │   └── ticket_notifications.py
│   ├── utils/                  # Shared utilities
│   │   ├── security.py         # JWT, password hashing, auth dependencies
│   │   ├── kafka.py            # Kafka producer singleton
│   │   ├── consumer.py         # Kafka consumer framework
│   │   ├── redis.py            # Redis SSE pub/sub streams
│   │   ├── pagination.py       # Cursor-based pagination utilities
│   │   ├── permissions.py      # Permission checking utilities
│   │   ├── log_manager.py      # Singleton logger (console + file rotation)
│   │   └── cookies.py          # Cookie configuration helper
│   ├── templates/              # HTML email templates (9 templates)
│   ├── tests/                  # Pytest test suite
│   ├── alembic/                # Database migration scripts
│   ├── grafana/                # Grafana provisioning configs
│   ├── Dockerfile              # Multi-stage build (builder → runtime)
│   ├── compose.yaml            # All services: FastAPI, PostgreSQL, Redis,
│   │                           # Kafka, Kafka UI, Prometheus, Grafana, Loki, Promtail
│   ├── pyproject.toml          # Python dependencies (managed by uv)
│   └── .pre-commit-config.yaml # Ruff linting/formatting + pytest
│
├── frontend/                   # Next.js 15 web application
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── page.tsx        # Landing page (hero, destinations, testimonials)
│   │   │   ├── flights/        # Flight search & results
│   │   │   ├── booking/        # Booking detail, payment, success
│   │   │   ├── auth/           # Login, register, forgot/reset password, Google OAuth
│   │   │   ├── admin/          # Admin dashboard & booking management
│   │   │   ├── my/             # User bookings ("My Bookings")
│   │   │   └── profile/        # User profile & settings
│   │   ├── components/         # Reusable React components
│   │   │   ├── BookingForm.tsx  # Flight search form with autocomplete
│   │   │   ├── SeatMap.tsx      # Interactive seat map viewer
│   │   │   ├── Navbar.tsx       # Navigation with auth state
│   │   │   ├── NotificationBell.tsx # Real-time notification dropdown (SSE)
│   │   │   ├── SignupModal.tsx  # Auth modal
│   │   │   └── ...             # Hero, Footer, Skeletons, etc.
│   │   ├── store/              # Zustand stores (auth, flights)
│   │   ├── hooks/              # Custom hooks (useAuth, useNotifications)
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Utility functions
│   ├── public/                 # Static assets (logo, favicons, hero images)
│   └── package.json            # npm dependencies
│
├── terraform/                  # AWS infrastructure as code
│   ├── main.tf                 # EC2 instance, security groups, Elastic IP
│   ├── variables.tf            # Input variables
│   ├── outputs.tf              # Output values (public IP)
│   └── terraform.tf            # Backend & provider config (S3 state)
│
├── .github/
│   └── workflows/
│       └── terraform.yml       # CI/CD: Terraform plan/apply + SSH deploy
│
├── mobile/                     # (Planned) Mobile application
└── shared/                     # (Planned) Shared resources
```

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose** (v2)
- **Node.js 20+** and **npm**
- **Python 3.12+** and [**uv**](https://docs.astral.sh/uv/)
- API credentials: [Amadeus](https://developers.amadeus.com/), [Pesapal](https://developer.pesapal.com/), [Cloudinary](https://cloudinary.com/), [Google Cloud Console](https://console.cloud.google.com/) (for OAuth)

### Backend Setup

```bash
cd backend

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys and secrets (see Environment Variables section)

# Start all services (FastAPI, PostgreSQL, Redis, Kafka, Prometheus, Grafana, Loki)
docker compose up --build
```

> The API will be available at **http://localhost:8000**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment variables
cp .env.example .env.local
# Ensure NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Start development server (with Turbopack)
npm run dev
```

> The app will be available at **http://localhost:3000**

### Management Commands

The backend includes a Typer-based CLI for user management:

```bash
# Create a superuser (full system access + admin group)
python -m backend.manage create-super-user

# Create an admin user (admin group permissions)
python -m backend.manage create-admin
```

> Both commands prompt for email and password with validation (email format, password strength: uppercase, lowercase, digit, minimum length).

---

## API Reference

Once the backend is running, interactive API documentation is available at:

| Format | URL |
|---|---|
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |

### API Endpoints Overview

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/users/register` | Register a new user |
| `POST` | `/users/login` | Login (returns JWT in HTTP-only cookie) |
| `POST` | `/users/logout` | Clear auth cookie |
| `POST` | `/users/forgot-password` | Request password reset email |
| `POST` | `/users/reset-password` | Reset password with token |
| `GET` | `/users/me` | Get current user info |
| `PUT` | `/users/change-password` | Change password |
| `GET` | `/auth/google` | Initiate Google OAuth login |
| `GET` | `/auth/google/callback` | Handle Google OAuth callback |
| `POST` | `/flights/search` | Search flights (POST body) |
| `GET` | `/flights/search` | Search flights (query params) |
| `POST` | `/flights/pricing` | Confirm flight pricing |
| `POST` | `/flights/order` | Create flight booking |
| `GET` | `/flights/order/{booking_id}` | Get booking details |
| `DELETE` | `/flights/order/{booking_id}` | Cancel flight booking |
| `GET` | `/flights/seatmap` | View seat map for booked flight |
| `GET` | `/flights/bookings` | Get user's bookings (cursor-paginated) |
| `GET` | `/flights/airport-city-search` | Airport/city autocomplete |
| `POST` | `/payments/initiate` | Initiate Pesapal payment |
| `GET` | `/payments/callback` | Pesapal redirect callback |
| `GET` | `/payments/ipn` | Pesapal IPN webhook |
| `GET` | `/payments/status/{id}` | Check payment status |
| `POST` | `/payments/refund` | Request refund |
| `POST` | `/tickets/upload/{booking_id}` | Upload ticket PDF (admin) |
| `GET` | `/notifications/` | List notifications (cursor-paginated) |
| `GET` | `/notifications/stream` | SSE notification stream |
| `GET` | `/notifications/unread-count` | Get unread count |
| `PUT` | `/notifications/mark-all-read` | Mark all as read |
| `GET` | `/admin/stats/bookings` | Booking statistics (admin) |
| `GET` | `/admin/bookings` | All bookings (admin, cursor-paginated) |
| `GET` | `/admin/bookings/{id}` | Booking detail (admin) |
| `GET` | `/health` | System health check |

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Security
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Amadeus Flight API
AMADEUS_API_KEY=<your-key>
AMADEUS_API_SECRET=<your-secret>
AMADEUS_BASE_URL=test.api.amadeus.com

# Pesapal Payment Gateway
PESAPAL_CONSUMER_KEY=<your-key>
PESAPAL_CONSUMER_SECRET=<your-secret>
PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
PESAPAL_IPN_ID=<your-ipn-id>

# Cloudinary (file uploads)
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>

# Redis
REDIS_URL=redis://redis:6379

# Email (SMTP)
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-app-password>
MAIL_FROM=<sender-email>
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Application
CORS_ORIGINS=http://localhost:3000,http://localhost
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WHATSAPP_NUMBER=<your-whatsapp-number>
```

---

## Event-Driven Architecture

The backend uses **Apache Kafka** as an event bus to decouple core operations from side effects like email notifications and in-app alerts.

### Event Flow

```
  API Router                 Kafka Producer              Kafka Consumer
 ┌──────────┐  publish()   ┌──────────────┐  consume()  ┌──────────────┐
 │ User     │ ───────────►│ user.events  │ ──────────► │ Send welcome │
 │ registers│              └──────────────┘             │ email + DB   │
 └──────────┘                                           │ notification │
                                                        └──────────────┘
 ┌──────────┐  publish()   ┌──────────────┐  consume()  ┌──────────────┐
 │ Booking  │ ───────────► │booking.events│ ──────────► │ Email user + │
 │ created  │              └──────────────┘             │ admin, SSE   │
 └──────────┘                                           │ push via     │
                                                        │ Redis Pub/Sub│
                                                        └──────────────┘
```

### Kafka Topics

| Topic | Events |
|---|---|
| `user.events` | `user_registered`, `password_reset_requested`, `password_changed` |
| `booking.events` | `booking_created`, `booking_cancelled` |
| `payment.events` | `payment_successful`, `payment_failed`, `refund_requested` |
| `ticket.events` | `ticket_uploaded` |

### Real-Time Notifications (SSE)

The frontend connects to SSE endpoints backed by **Redis Pub/Sub**. When a Kafka consumer processes an event, it:

1. Saves a `Notification` record in PostgreSQL
2. Publishes the notification to a user-specific Redis channel
3. The SSE stream picks it up and delivers it to the connected client

Heartbeats are sent every 30 seconds to keep connections alive.

---

## Observability

The `compose.yaml` includes a full observability stack:

| Service | Port | Purpose |
|---|---|---|
| **Prometheus** | `9090` | Scrapes FastAPI metrics via `prometheus-fastapi-instrumentator` |
| **Grafana** | `3001` | Dashboards, alerting (default credentials: `admin/admin`) |
| **Loki** | `3100` | Log aggregation backend |
| **Promtail** | — | Ships `backend.log` to Loki |
| **Kafka UI** | `8080` | Inspect Kafka topics, consumers, and messages |

The backend uses a **singleton LogManager** with:
- Console output (`stdout`)
- Time-rotating file handler (`.logs/backend.log`, 7-day retention)
- Security logging from `fastapi-guard` middleware

---

## CI/CD & Deployment

The project uses a single **GitHub Actions workflow** (`.github/workflows/terraform.yml`) that handles both infrastructure and application deployment.

### Pipeline Flow

```
Pull Request → Terraform Plan (review)
Main Branch Push → Terraform Apply → SSH Deploy to EC2
```

### Deployment Steps (on push to `main`)

1. **Terraform Apply** — provisions/updates AWS EC2 instance, security groups, and Elastic IP
2. **SSH into EC2** — installs Docker/Git if needed, creates swap space
3. **Clone/Pull** — fetches latest code from the repository
4. **Generate `.env`** — injects secrets from GitHub Actions environment
5. **Docker Compose** — rebuilds and restarts all containers
6. **Nginx Setup** — configures reverse proxy for `api.aeroboundventures.com`
7. **SSL** — Certbot auto-configures HTTPS certificates

### Infrastructure

- **EC2**: Ubuntu 24.04, 16GB disk, configurable instance type
- **Security Groups**: Ports 80 (HTTP), 443 (HTTPS), 22 (SSH)
- **Elastic IP**: Stable public IP for DNS
- **Nginx**: Reverse proxy to `localhost:8000` with SSL termination

---

## Testing & Code Quality

### Running Tests

```bash
cd backend
pytest
```

The test suite covers:
- Consumer event handlers
- CRUD operations
- External service integrations
- Health check endpoints
- Cursor-based pagination
- Password reset flow
- Seat map logic

### Pre-Commit Hooks

The backend uses [pre-commit](https://pre-commit.com/) with:
- **Ruff** — linting (`ruff-check --fix`) and formatting (`ruff-format`)
- **Pytest** — runs the full test suite before each commit

```bash
cd backend
pre-commit run --all-files
```

### Database Migrations

```bash
cd backend
alembic upgrade head      # Apply all pending migrations
alembic revision --autogenerate -m "description"  # Generate new migration
```

---

## License

MIT