FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/app ./app
# Install the exact, reviewed production resolution. The lockfile is copied
# before the application source so dependency layers stay reusable while a
# source-only change cannot silently upgrade a runtime package.
RUN pip install --no-cache-dir uv==0.8.17 \
  && uv sync --frozen --no-dev
COPY --from=web /web/dist /app/static
RUN useradd --create-home --uid 10001 driftline \
  && chown -R driftline:driftline /app
USER driftline
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DRIFTLINE_STATIC_DIR=/app/static
ENV PATH="/app/.venv/bin:${PATH}"
CMD exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT}
