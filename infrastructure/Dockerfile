# ============================================================
# KynicOS — Dockerfile
# Multi-stage, mínimo, sin secretos en imagen
# ============================================================

FROM python:3.12-slim AS builder

# Dependencias de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Poetry solo para resolver dependencias → requirements.txt
RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt 2>/dev/null || \
    poetry install --only main --no-root

# ── Runtime ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar deps desde builder
COPY --from=builder /build/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Copiar app
COPY app/ ./app/
COPY workspace/ ./workspace/
COPY config/ ./config/
COPY web/ ./web/

# Volumen de datos runtime (sesiones, memoria dinámica)
RUN mkdir -p /app/data/sessions /app/workspace/logic /app/workspace/skills

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/status || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
