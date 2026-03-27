# Repository Guidelines

## Project Structure & Module Organization
This repository is split by surface area. `frontend/` contains the Next.js app; primary code lives in `frontend/src/` with routes under `src/app/`, shared UI in `src/components/`, and state/utilities in `src/store/`, `src/hooks/`, and `src/lib/`. `backend/` contains the FastAPI service with routers in `backend/routers/`, persistence in `backend/crud/` and `backend/models/`, schemas in `backend/schemas/`, Kafka consumers in `backend/consumers/`, and tests in `backend/tests/`. Infrastructure code lives in `terraform/`. Treat `mobile/` and `shared/` as reserved workspace areas unless a task explicitly targets them.

## Build, Test, and Development Commands
- `cd frontend && npm install && npm run dev`: start the web app with Turbopack.
- `cd frontend && npm run build`: create a production build.
- `cd frontend && npm run lint`: run Next.js ESLint checks.
- `cd backend && uv sync`: install Python dependencies from `pyproject.toml`.
- `cd backend && uv run fastapi dev main.py`: run the API locally.
- `cd backend && uv run pytest`: run the backend test suite.
- `cd backend && docker compose up -d --build`: start the full local stack.
- `terraform -chdir=terraform validate` and `terraform -chdir=terraform plan`: verify infra changes before review.

## Coding Style & Naming Conventions
Python uses 4-space indentation, snake_case modules, and Ruff for linting/formatting via `backend/.pre-commit-config.yaml`. TypeScript/React follows the existing code style in `frontend/src/`: 2-space indentation, PascalCase component files such as `HeroSection.tsx`, and colocated route folders under `src/app/`. Prefer descriptive names tied to domain concepts like `bookings`, `payments`, and `notifications`.

## Testing Guidelines
Backend tests use `pytest` with filenames like `test_bookings.py` and shared fixtures in `backend/tests/conftest.py`. Add or update tests whenever router, CRUD, consumer, or integration behavior changes. There is no established frontend test suite yet, so run `npm run lint` and document manual UI verification in the PR.

## Commit & Pull Request Guidelines
Recent history follows concise, imperative commit subjects, usually Conventional Commit style: `fix(admin): exclude cancelled bookings from revenue`. Keep commits scoped by area (`frontend`, `backend`, `admin`, `auth`). PRs should include a short problem statement, the change summary, linked issue if available, and screenshots for visible frontend changes. Call out env, schema, or Terraform impacts explicitly before requesting review.

## Security & Configuration Tips
Do not commit `.env` files, API secrets, cloud credentials, or Terraform state. Backend changes often depend on external services and cookies/CORS settings, so document any new environment variables in the relevant README and verify safe defaults before merging.
