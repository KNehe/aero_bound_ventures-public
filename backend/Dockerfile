FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /backend

# Copy the application into the container.
COPY . .

# Install the application dependencies.
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 80