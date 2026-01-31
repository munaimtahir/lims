#!/bin/bash
set -e

echo "Starting infrastructure manually since docker compose is unavailable..."

# Create network if not exists
docker network inspect lims_network >/dev/null 2>&1 || docker network create lims_network

# Start Redis
if [ ! "$(docker ps -q -f name=lims_redis)" ]; then
    if [ "$(docker ps -aq -f name=lims_redis)" ]; then
        echo "Removing stopped redis container..."
        docker rm lims_redis
    fi
    echo "Starting Redis..."
    docker run -d --name lims_redis \
        --network lims_network \
        --health-cmd "redis-cli ping" \
        --health-interval 10s \
        --health-retries 5 \
        redis:7-alpine redis-server --appendonly yes --requirepass ""
fi

# Start DB
if [ ! "$(docker ps -q -f name=lims_db)" ]; then
    if [ "$(docker ps -aq -f name=lims_db)" ]; then
        echo "Removing stopped db container..."
        docker rm lims_db
    fi
    echo "Starting Database..."
    docker run -d --name lims_db \
        --network lims_network \
        -e POSTGRES_DB=lims_db \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=changeme \
        --health-cmd "pg_isready -U postgres" \
        --health-interval 10s \
        --health-retries 5 \
        postgres:16-alpine
fi

# Build Backend
echo "Building backend image..."
docker build -t lims_backend ./lims-backend

# Start Backend
if [ ! "$(docker ps -q -f name=lims_backend)" ]; then
    if [ "$(docker ps -aq -f name=lims_backend)" ]; then
        echo "Removing stopped backend container..."
        docker rm lims_backend
    fi
    echo "Starting Backend..."
    
    # Ensure logs dir exists
    mkdir -p ./logs

    docker run -d --name lims_backend \
        --network lims_network \
        -v $(pwd)/lims-backend:/app \
        -v $(pwd)/logs:/app/logs \
        -e SECRET_KEY="django-insecure-test-key-must-override-in-prod" \
        -e DB_ENGINE=django.db.backends.postgresql \
        -e DB_NAME=lims_db \
        -e DB_USER=postgres \
        -e DB_PASSWORD=changeme \
        -e DB_HOST=lims_db \
        -e DB_PORT=5432 \
        -e REDIS_URL=redis://lims_redis:6379/0 \
        -e DEBUG=True \
        -e ALLOWED_HOSTS="*" \
        -e CELERY_BROKER_URL=redis://lims_redis:6379/0 \
        -e DJANGO_SETTINGS_MODULE=config.settings.production \
        lims_backend
fi

echo "Infrastructure started."
