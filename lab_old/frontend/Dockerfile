# ==============================================================================
# Frontend Dockerfile - For Development Use
# ==============================================================================
# This Dockerfile is used by infra/docker-compose.yml for local development.
# The build creates a production-ready image, but the dev docker-compose
# overrides the CMD to run `pnpm dev --host` with volume mounts for hot reload.
#
# For production deployment, use nginx/Dockerfile which builds a multi-stage
# image that includes both frontend and backend static files.
# ==============================================================================

# Stage 1: Build the frontend (also used as base for dev with command override)
FROM node:20-slim AS builder

WORKDIR /app

# Install pnpm (matching version from package.json)
RUN npm install -g pnpm@8.15.9

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build the application (creates dist directory)
# NOTE: For dev usage, this is skipped as the command is overridden
RUN pnpm build

# Stage 2: Serve with nginx (production image - not used in dev)
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# nginx runs in foreground by default
CMD ["nginx", "-g", "daemon off;"]
