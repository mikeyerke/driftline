FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .
COPY --from=web /web/dist /app/static
RUN useradd --create-home --uid 10001 driftline \
  && chown -R driftline:driftline /app
USER driftline
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DRIFTLINE_STATIC_DIR=/app/static
CMD exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT}
