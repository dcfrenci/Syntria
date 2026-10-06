ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTAPI_PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${FASTAPI_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${FASTAPI_PORT} --proxy-headers"]