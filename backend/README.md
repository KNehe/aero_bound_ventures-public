# Aero Bound Ventures Backend

FastAPI backend for Aero Bound Ventures. The backend reads standard environment variables, so Doppler can be used as the runtime secret injector for local development, GitHub Actions, and EC2 without changing application code.

## Doppler Setup

### 1. Install and authenticate the Doppler CLI

```bash
doppler login
```

Official docs:
- https://docs.doppler.com/docs/install-cli
- https://docs.doppler.com/docs/accessing-secrets

### 2. Bind the backend directory to a Doppler project/config

Recommended structure:
- Project: `aero-bound-ventures-backend`
- Configs: `dev`, `stg`, `prd`

```bash
cd backend
doppler setup
```

### 3. Seed the expected secret keys

Use [`.env.example`](./.env.example) as the schema for the backend secrets:

```bash
cd backend
doppler secrets upload .env.example
```

Then replace placeholder values in Doppler with real values.

## Running Locally

The backend image can start with plain environment variables, which is the
runtime contract Kubernetes will use later. The image still includes the Doppler
CLI for compatibility, and local Docker Compose wraps the app command with
`doppler run`.

For local Docker development, create a short-lived service token right before you start the stack:

```bash
cd backend
export DOPPLER_TOKEN="$(doppler configs tokens create docker --max-age 15m --plain)"
doppler run -- docker compose up --build
```

The docs show `1m` as an example, but `15m` is safer for `docker compose up --build` because the image build can take longer than a minute.

If you only want the backend core services, skip the observability stack:

```bash
cd backend
export DOPPLER_TOKEN="$(doppler configs tokens create docker --max-age 15m --plain)"
doppler run -- docker compose up --build fastapi-app notification-worker db redis kafka
```

The single Compose file is used locally and on EC2. It does not mount host
source code into backend containers. Rebuild after code changes so local Compose,
local Kubernetes, and EC2 all test the immutable image produced by the Dockerfile.

You can also build and inspect the backend image without Doppler:

```bash
# From the repository root
docker build -t aero-backend:local backend
docker run --rm aero-backend:local python --version
docker run --rm aero-backend:local fastapi --version
```

You can also run backend commands directly on the host with Doppler injected at runtime:

```bash
cd backend
doppler run -- uv run fastapi dev main.py
doppler run -- uv run pytest
doppler run -- uv run python manage.py create-admin
```

## Runtime Processes

The backend image provides two separate process types:

- `fastapi run main.py` serves HTTP and publishes Kafka events.
- `python -m backend.worker` consumes Kafka events and sends notifications.

Run either process directly from the repository root:

```bash
backend/.venv/bin/fastapi dev backend/main.py
backend/.venv/bin/python -m backend.worker
```

Docker Compose runs both as separate services from `aero-backend:local`.
Kubernetes will use the image's default FastAPI command for the API Deployment
and override the command to `python -m backend.worker` for the worker Deployment.

`fastapi-app` owns the Compose build configuration. To start only the worker on
a machine where the image has not been built yet, build the shared image first:

```bash
cd backend
docker compose build fastapi-app
docker compose up notification-worker
```

## Deployment

This repository deploys to EC2 through [`.github/workflows/terraform.yml`](../.github/workflows/terraform.yml).

The deployment flow is:
- Terraform creates or updates the EC2 instance and Elastic IP.
- GitHub Actions SSHes into the EC2 host.
- The workflow installs Docker and the Doppler CLI if missing.
- The backend is started on the host with Docker Compose. Compose passes
  `DOPPLER_TOKEN` into both backend containers and wraps the API and worker
  commands with `doppler run`:

```bash
sudo --preserve-env=DOPPLER_TOKEN doppler run -- docker compose up -d --build
```

EC2 and local development intentionally use the same `compose.yaml` file and the
same immutable backend image. Kubernetes will replace the EC2 orchestration only
after the image and Helm deployment pass local Kubernetes validation.

Required GitHub secret for backend runtime secrets:
- `DOPPLER_TOKEN`

That token should be a Doppler service token scoped only to the backend production config.

Required GitHub secret for AWS authentication in GitHub Actions:
- `AWS_ROLE_TO_ASSUME`

Create that IAM role manually in AWS with a trust policy that allows GitHub Actions OIDC for this repository, and attach the IAM permissions needed for Terraform state access plus the EC2 actions this stack uses. Then paste the role ARN into the secret.
The workflow uses that role with `aws-actions/configure-aws-credentials`, so long-lived AWS access keys are not needed in GitHub Secrets.

The workflow also resolves the Certbot contact email from the Doppler secret `MAIL_FROM`, so that value no longer needs to be duplicated as a separate GitHub Actions secret.
Make sure the backend production config also sets `CORS_ORIGINS` to the frontend origin(s) you serve, for example `https://www.aeroboundventures.com,https://aeroboundventures.com`.

### Guard Core dashboard telemetry

Guard Core telemetry is enabled for this app. Create an API key in the dashboard and add this secret to the backend Doppler config:

```env
GUARD_API_KEY=<guard-core-api-key>
PASSIVE_MODE=true
```

Encryption is disabled for the current Guard Core API key, so no project encryption key is configured. Keep `PASSIVE_MODE=true` during the first rollout so detections and metrics are visible without blocking user traffic.
The Guard Agent endpoint is configured in code as `https://api.guard-core.com`.

For direct host usage outside GitHub Actions:

```bash
cd /opt/aero_bound_ventures/backend
export DOPPLER_TOKEN='dp.st.prd.xxxx'
doppler run -- docker compose up -d --build
```

Practical notes:
- Keep the service token outside the repo.
- Scope it to the backend production config only.
- Inject the token from your deployment platform or workflow.
- Rotate the service token independently from app secrets.

## Notes For This Codebase

- The backend still supports plain environment variables, so Doppler is an injection layer, not a rewrite.
- The Docker image default command starts FastAPI directly. Docker Compose adds
  the local Doppler wrapper and starts a separate notification worker through
  `backend/compose.yaml`.
- Several modules call `load_dotenv()`. That does not conflict with Doppler.
- Avoid committing `.env` files. The repository root `.gitignore` already excludes them.

## Useful Commands

```bash
cd backend

# Inspect which project/config this directory is bound to
doppler configure --scope .

# Print resolved secrets in env format without writing a file
doppler secrets download --no-file --format env

# Run alembic with Doppler
doppler run -- uv run alembic upgrade head
```

## License

MIT
