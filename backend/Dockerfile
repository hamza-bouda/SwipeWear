FROM python:3.11-slim AS base

# System packages required by psycopg2 (compiled driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "."

# Copy source
COPY . .

EXPOSE 8000

# run_migrations.py applies all SQL migrations before starting uvicorn.
# PORT is injected by Railway; falls back to 8000 for local docker run.
CMD ["sh", "-c", "python scripts/run_migrations.py && uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
