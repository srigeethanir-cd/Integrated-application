FROM python:3.12-slim

# Install system dependencies for Playwright, OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and pre-install CPU-only libraries to keep image size small
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir paddlepaddle

# Copy requirements
COPY backend/requirements.txt ./backend/
COPY backend/requirements-ml.txt ./backend/

# Install python requirements
RUN pip install --no-cache-dir -r backend/requirements.txt -r backend/requirements-ml.txt

# Install Playwright browser executables and OS-level dependencies (specifically chromium)
RUN playwright install --with-deps chromium

# Copy code components
COPY backend/ ./backend/
COPY human_execution/ ./human_execution/
COPY ml/ ./ml/
COPY services/ ./services/

ENV PYTHONPATH=/app

WORKDIR /app/backend

EXPOSE 8006

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8006"]
