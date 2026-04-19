# Dockerfile for Render (or any container registry)
FROM python:3.12-slim

WORKDIR /app

# Install system deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./

# Ensure pip, wheel and a known setuptools are present/installed into the same interpreter
# Install a pinned setuptools first (strong guarantee pkg_resources will be available),
# then install the rest of the requirements and verify pkg_resources can be imported.
RUN python -m pip install --upgrade pip wheel setuptools==68.0.0 && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    python -c "import pkg_resources; print('pkg_resources ok:', pkg_resources.__file__)"

# Copy app
COPY . .

# Expose port (Render provides $PORT at runtime)
EXPOSE 8000

# Use Gunicorn with Uvicorn workers; bind to Render's $PORT env var at runtime
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--log-level", "info"]
