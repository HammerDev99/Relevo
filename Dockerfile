# syntax=docker/dockerfile:1
# ============================================================================
# Relevo: Dockerfile de producción (alineado con estándares Sherlock-docs)
# 2-stage build con BuildKit cache mounts y patrón gosu
# ============================================================================

# Stage 1: Builder
FROM python:3.12-slim-bookworm@sha256:31c0807da611e2e377a2e9b566ad4eb038ac5a5838cbbbe6f2262259b5dc77a0 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Crear virtualenv aislado
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README-deploy.md ./
# Dummy structure for pip install metadata resolution
RUN mkdir -p src/app src/relevo && touch src/app/__init__.py src/relevo/__init__.py

# Instalar dependencias con cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install .

# Stage 2: Runtime
FROM python:3.12-slim-bookworm@sha256:31c0807da611e2e377a2e9b566ad4eb038ac5a5838cbbbe6f2262259b5dc77a0 AS runtime

# Binarios de runtime: curl para healthcheck + gosu para privilegios
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gosu \
    && rm -rf /var/lib/apt/lists/*

# Copiar virtualenv del builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copiar código fuente
COPY src/ src/

# SEC-03: Crear usuario no-root
RUN useradd -m -u 1000 -s /bin/bash relevo

# Configuración de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/src
ENV DATABASE_URL=sqlite:////app/data/database/relevo.db
ENV TZ=America/Bogota

# Directorios de datos y logs
RUN mkdir -p data/database logs \
    && chown -R relevo:relevo /app

# Copiar entrypoint y healthcheck
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY docker-healthcheck.sh /docker-healthcheck.sh
RUN chmod +x /docker-entrypoint.sh /docker-healthcheck.sh

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/docker-healthcheck.sh"]

ENTRYPOINT ["/docker-entrypoint.sh"]

# Fallback CMD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
