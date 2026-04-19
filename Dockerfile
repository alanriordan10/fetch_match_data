# Dockerfile for Render (or any container registry)
FROM python:3.12-slim

WORKDIR /app

# Install system deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./

# Ensure pip, setuptools and wheel are present/up-to-date so pkg_resources exists for gunicorn
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port (Render provides $PORT at runtime)
EXPOSE 8000

# Use Gunicorn with Uvicorn workers; bind to Render's $PORT env var at runtime
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--log-level", "info"]
