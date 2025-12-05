# LIMS Deployment Guide

This guide covers deploying the LIMS (Laboratory Information Management System) application.

## Prerequisites

- Docker and Docker Compose installed
- At least 2GB RAM available
- Domain name (for production deployment)

## Local Development with Docker

### 1. Clone the repository

```bash
git clone https://github.com/your-org/LIMS_new.git
cd LIMS_new
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```bash
# Required
SECRET_KEY=your-secure-secret-key-here
DB_PASSWORD=your-database-password

# Optional
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost
```

### 3. Build and start services

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost/api/v1/
- API Docs: http://localhost/api/docs/
- Admin: http://localhost/admin/

### 4. Run migrations and create superuser

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load sample data (optional)
docker-compose exec backend python create_sample_data.py
```

## Production Deployment (VPS)

### 1. Server setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### 2. Deploy application

```bash
# Clone repository
git clone https://github.com/your-org/LIMS_new.git
cd LIMS_new

# Create production environment file
cat > .env << EOF
SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
EOF

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user
docker-compose exec backend python manage.py createsuperuser
```

### 3. Enable HTTPS (production)

Update the Caddyfile to use your domain:

```caddyfile
your-domain.com {
    # Same configuration as :80
    # Caddy automatically handles SSL certificates
}
```

Restart the proxy:

```bash
docker-compose restart proxy
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| SECRET_KEY | Django secret key | Yes |
| DB_PASSWORD | PostgreSQL password | Yes |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts | Yes (production) |
| CORS_ALLOWED_ORIGINS | Comma-separated CORS origins | Yes (production) |
| DEBUG | Enable debug mode (default: False) | No |
| EMAIL_HOST_USER | SMTP username | No |
| EMAIL_HOST_PASSWORD | SMTP password | No |

### Default Users

After running `create_sample_data.py`:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| receptionist | recep123 | Receptionist |
| pathologist | patho123 | Pathologist |

## Maintenance

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Backup database

```bash
docker-compose exec db pg_dump -U postgres lims_db > backup.sql
```

### Restore database

```bash
docker-compose exec -T db psql -U postgres lims_db < backup.sql
```

### Update application

```bash
git pull
docker-compose up --build -d
docker-compose exec backend python manage.py migrate
```

## Troubleshooting

### Container not starting

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs backend
```

### Database connection issues

Ensure the database is healthy:

```bash
docker-compose exec db pg_isready -U postgres
```

### Static files not loading

```bash
docker-compose exec backend python manage.py collectstatic --noinput
docker-compose restart proxy
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Caddy Proxy                          │
│                    (SSL termination)                        │
└─────────────────────────────────────────────────────────────┘
                     │                    │
                     ▼                    ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│   Frontend (React)      │    │   Backend (Django)       │
│   Served by Nginx       │    │   Gunicorn WSGI         │
└─────────────────────────┘    └─────────────────────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                   ┌─────────────────────┐  ┌─────────────────┐
                   │   PostgreSQL        │  │   Redis         │
                   │   Database          │  │   Cache/Broker  │
                   └─────────────────────┘  └─────────────────┘
```

## Support

For issues and feature requests, please open an issue on GitHub.
