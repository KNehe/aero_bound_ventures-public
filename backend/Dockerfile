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

RUN apt-get update && apt-get install -y --no-install-recommends apt-transport-https ca-certificates curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" > /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && apt-get install -y --no-install-recommends doppler && \
    rm -rf /var/lib/apt/lists/*

ENV DOPPLER_CONFIG_DIR=/tmp/.doppler

COPY --from=builder /app/backend /app/backend

CMD ["doppler", "run", "--", "/app/backend/.venv/bin/fastapi", "run", "main.py", "--port", "80", "--host", "0.0.0.0"]
