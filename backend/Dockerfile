# --- Stage 1: Build -----
FROM python:3.12-slim AS builder

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/backend

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY . .

# --- Stage 2: Runtime -----
FROM python:3.12-slim AS runtime

WORKDIR /app/backend

COPY --from=builder /app/backend /app/backend

# Run the application.
CMD ["/app/backend/.venv/bin/fastapi", "run", "main.py", "--port", "80", "--host", "0.0.0.0"]