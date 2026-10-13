ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NICEGUI_PORT=${NICEGUI_PORT} \
    NICEGUI_STORAGE_PATH=/data/nicegui \
    HOME=/tmp

WORKDIR /app

COPY requirements.lock .
RUN pip install -r requirements.lock

RUN useradd --system --uid 10001 --no-create-home appuser \
 && mkdir -p /data/nicegui && chown appuser:appuser /data/nicegui
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8080
CMD ["python", "app/main.py"]