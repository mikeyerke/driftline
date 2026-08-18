FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
ENV PORT=8080
CMD exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT}

