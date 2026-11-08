# syntax=docker/dockerfile:1

# ─── Stage 1: Angular frontend ────────────────────────────────────────────
FROM node:24-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python dependencies ─────────────────────────────────────────
FROM python:3.14-alpine AS backend-builder

COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app/backend
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    uv sync --locked --no-dev

# ─── Stage 3: runtime ─────────────────────────────────────────────────────
FROM python:3.14-alpine

RUN apk add --no-cache curl \
    && addgroup -S -g 1000 app \
    && adduser -S -D -H -u 1000 -G app app \
    && mkdir -p /var/lib/app \
    && chown app:app /var/lib/app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/var/lib/app \
    FRONTEND_DIR=/app/frontend \
    # One worker by default; Uvicorn reads WEB_CONCURRENCY as its worker count
    WEB_CONCURRENCY=1

WORKDIR /app/backend
COPY --from=backend-builder /app/.venv /app/.venv
COPY --from=frontend-builder /build/frontend/dist/frontend/browser /app/frontend
COPY backend/app ./app

ARG VERSION=dev
ENV APP_VERSION=${VERSION}

USER app
VOLUME ["/var/lib/app"]
EXPOSE 8000/tcp

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
