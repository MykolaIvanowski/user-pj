# syntax=docker/dockerfile:1.6
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (curl for healthcheck, build-essential only if needed for bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better caching.
# Support both pyproject.toml and requirements.txt
COPY requirements.txt* pyproject.toml* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi \
    && if [ -f pyproject.toml ]; then pip install --no-cache-dir .; fi

COPY app ./app
# If you have alembic/migrations, uncomment:
# COPY alembic* ./alembic*
# COPY migrations ./migrations

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
