# App image for Cloud Run: built frontend + FastAPI backend in one container (same origin).
# Build context = repo root.

# ---- 1. Build the React frontend ----
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_CHAT_API_URL=/api
RUN npm run build

# ---- 2. Python backend ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .

COPY backend/data ./data
COPY --from=web /web/dist ./static

ENV DATA_DIR=/app/data \
    STATIC_DIR=/app/static \
    SESSION_HTTPS_ONLY=true \
    PORT=8080

RUN useradd --create-home appuser && chown -R appuser /app/data
USER appuser

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
