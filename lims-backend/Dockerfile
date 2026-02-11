# Backend Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ARG DJANGO_SETTINGS_MODULE=config.settings.development
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    zip \
    tar \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (production set includes gunicorn/logging deps)
COPY requirements/base.txt requirements/production.txt requirements/development.txt requirements/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/production.txt

# Bootstrap helper
COPY bootstrap_prod.sh /app/bootstrap_prod.sh
RUN chmod +x /app/bootstrap_prod.sh

# Copy project
COPY . .

# Create static files directory
RUN mkdir -p staticfiles media

# Static files are collected at runtime in bootstrap_prod.sh to ensure sync with volumes
# (Avoiding build-time collection which can be shadowed by mounted volumes)

# Create non-root user
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID -o appuser
RUN useradd -m -u $UID -g $GID -o -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run bootstrap then gunicorn (command overridable for celery)
CMD ["/app/bootstrap_prod.sh", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
