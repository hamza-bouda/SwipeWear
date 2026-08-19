FROM python:3.11-slim AS base

# System packages required by psycopg2 (compiled driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Copy source
COPY . .

FROM base AS runtime-ai
RUN pip install --no-cache-dir -e ".[ai]"

FROM base AS runtime

EXPOSE 8000

# Migrations are a separate deployment unit in docker-compose. Railway still
# uses this safe standalone command because it deploys a single service.
CMD ["sh", "-c", "python scripts/run_migrations.py && uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
