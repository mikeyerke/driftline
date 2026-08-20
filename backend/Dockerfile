FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY app ./app
# Keep the standalone backend image on the same reviewed resolution as the
# production root image. A source-only change cannot silently upgrade runtime
# dependencies, and an out-of-date lockfile fails the frozen sync.
RUN pip install --no-cache-dir uv==0.8.17 \
  && uv sync --frozen --no-dev
RUN useradd --create-home --uid 10001 driftline \
  && chown -R driftline:driftline /app
USER driftline
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:${PATH}"
ENV PORT=8080
CMD exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT}
