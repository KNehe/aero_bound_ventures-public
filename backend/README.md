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

The backend image includes the Doppler CLI and starts the app through `doppler run`.

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
doppler run -- docker compose up fastapi-app db redis kafka
```

You can also run backend commands directly on the host with Doppler injected at runtime:

```bash
cd backend
doppler run -- uv run fastapi dev main.py
doppler run -- uv run pytest
doppler run -- uv run python manage.py create-admin
```

## Deployment

This repository deploys to EC2 through [`.github/workflows/terraform.yml`](../.github/workflows/terraform.yml).

The deployment flow is:
- Terraform creates or updates the EC2 instance and Elastic IP.
- GitHub Actions SSHes into the EC2 host.
- The workflow installs Docker and the Doppler CLI if missing.
- The backend is started on the host with:

```bash
sudo --preserve-env=DOPPLER_TOKEN doppler run -- docker compose up -d --build
```

Required GitHub secret for backend runtime secrets:
- `DOPPLER_TOKEN`

That token should be a Doppler service token scoped only to the backend production config.

Required GitHub secret for AWS authentication in GitHub Actions:
- `AWS_ROLE_TO_ASSUME`

Create that IAM role manually in AWS with a trust policy that allows GitHub Actions OIDC for this repository, and attach the IAM permissions needed for Terraform state access plus the EC2 actions this stack uses. Then paste the role ARN into the secret.
The workflow uses that role with `aws-actions/configure-aws-credentials`, so long-lived AWS access keys are not needed in GitHub Secrets.

The workflow also resolves the Certbot contact email from the Doppler secret `MAIL_FROM`, so that value no longer needs to be duplicated as a separate GitHub Actions secret.
Make sure the backend production config also sets `CORS_ORIGINS` to the frontend origin(s) you serve, for example `https://www.aeroboundventures.com,https://aeroboundventures.com`.

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
- Several modules call `load_dotenv()`. That does not conflict with Doppler.
- Avoid committing `.env` files. The repository root `.gitignore` already excludes them.
- When the backend sits behind Nginx or another reverse proxy, `TRUSTED_PROXIES` is auto-detected from the container gateway if the env var is unset. Set it explicitly only if you need to pin a different proxy IP or CIDR.
- The current guard defaults are tuned to reduce false positives: `AUTO_BAN_THRESHOLD=10` and `AUTO_BAN_DURATION=3600`.
- Use route-level `detection_exclusion(...)` for legitimate URL-like values such as OAuth `scope` and Pesapal `callback_url`.
- The EC2 deploy script clears `guard_core:banned_*` keys from Redis after each rollout so stale IP bans do not survive a fresh deployment.
- The public root route (`/`) and `/health` are explicitly bypassed from guard checks so they stay reachable for users and monitoring even if a client IP is banned elsewhere.

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
