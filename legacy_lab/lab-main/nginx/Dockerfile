# Stage 1: Build the frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Install pnpm (matching version from frontend/package.json)
# Note: strict-ssl=false is needed for CI/CD environments with self-signed certificates.
# For production, consider configuring proper SSL certificates instead.
RUN npm config set strict-ssl false && npm install -g pnpm@8.15.9

# Copy frontend package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
# Note: strict-ssl=false is needed for CI/CD environments with self-signed certificates.
# For production, consider configuring proper SSL certificates instead.
RUN pnpm config set strict-ssl false && pnpm install --frozen-lockfile

# Copy frontend application code
COPY frontend/ ./

# Production API URL configuration
# ARG allows override at build time: docker build --build-arg VITE_API_URL=/api
# Default: /api (nginx proxies /api/* to backend:8000 internally)
# This ensures the frontend uses the correct API path for the deployment environment
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

# Create .env for production build
RUN echo "VITE_API_URL=${VITE_API_URL}" > .env

# Build the application in production mode (creates dist directory)
# Uses .env.production and the VITE_API_URL env var set above
RUN pnpm build

# Stage 2: Build backend and collect static files
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Collect static files (creates /app/staticfiles with Django admin CSS/JS)
# Set SECRET_KEY for build time (collectstatic doesn't need real secret or DB)
ENV DJANGO_SECRET_KEY=build-time-secret-key-for-collectstatic
RUN python manage.py collectstatic --noinput

# Stage 3: Serve with nginx
FROM nginx:alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy built frontend files from frontend-builder stage
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy Django static files from backend-builder stage
COPY --from=backend-builder /app/staticfiles /app/staticfiles

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Expose ports
EXPOSE 80 443

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# nginx runs in foreground by default
CMD ["nginx", "-g", "daemon off;"]
