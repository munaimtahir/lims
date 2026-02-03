# Backend Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ARG SECRET_KEY
ARG DB_PASSWORD
ARG ALLOWED_HOSTS
ARG CORS_ALLOWED_ORIGINS
ARG CSRF_TRUSTED_ORIGINS
ENV SECRET_KEY=${SECRET_KEY}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV ALLOWED_HOSTS=${ALLOWED_HOSTS}
ENV CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
ENV CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt requirements/production.txt requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Bootstrap helper
COPY bootstrap_prod.sh /app/bootstrap_prod.sh
RUN chmod +x /app/bootstrap_prod.sh

# Copy project
COPY . .

# Create static files directory
RUN mkdir -p staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput

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
