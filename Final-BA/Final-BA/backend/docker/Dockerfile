# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements-base.txt /tmp/requirements-base.txt
COPY backend/requirements-ml.txt /tmp/requirements-ml.txt
COPY backend/mcp_server/requirements.txt /tmp/requirements-mcp.txt
COPY framework /tmp/framework

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /tmp/requirements-base.txt \
    && pip install -r /tmp/requirements-mcp.txt \
    && pip install -r /tmp/requirements-ml.txt \
    && pip install /tmp/framework \
    && rm -rf /tmp/requirements-base.txt /tmp/requirements-ml.txt /tmp/requirements-mcp.txt /tmp/framework

COPY backend /app
RUN chmod +x /app/scripts/start.sh

EXPOSE 8000

CMD ["sh", "/app/scripts/start.sh"]
