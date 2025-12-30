FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
# Note: --trusted-host is needed for CI/CD environments with self-signed certificates.
# For production, consider configuring proper SSL certificates instead.
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
# Collect static files (creates /app/staticfiles with Django admin CSS/JS)
# Set SECRET_KEY for build time (collectstatic doesn't need real secret or DB)
ENV DJANGO_SECRET_KEY=build-time-secret-key-for-collectstatic
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Add healthcheck
# === FIX 1 ===
# The "|| exit 1" must be on the same line as the CMD.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# === FIX 2 ===
# Run migrations and start gunicorn.
# The seed_data command has been removed as it is not idempotent
# and should be run manually after deployment, as per README.md.
CMD python manage.py migrate && \
    gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${WORKERS:-$((2 * $(nproc) + 1))} --timeout 120 --access-logfile - --error-logfile -
