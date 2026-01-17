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
ENV SECRET_KEY=${SECRET_KEY}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV ALLOWED_HOSTS=${ALLOWED_HOSTS}
ENV CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}

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

# Copy project
COPY . .

# Create static files directory
RUN mkdir -p staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run gunicorn (bind to localhost only - accessed via Caddy reverse proxy)
CMD ["gunicorn", "--bind", "127.0.0.1:8000", "--workers", "4", "config.wsgi:application"]
