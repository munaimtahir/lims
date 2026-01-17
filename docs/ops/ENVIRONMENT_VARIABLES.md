# Environment Variables Documentation

This document describes all environment variables used by the LIMS application.

## Quick Start

For **development**, the `setup.sh` script automatically creates a `.env` file with sensible defaults. You don't need to configure anything manually.

For **production**, you must set the required environment variables explicitly.

> **Note**: The setup script (`setup.sh`) handles all environment variable setup for development. For production, see the Production Setup section below.

## Backend Environment Variables

### Required Variables

These variables are **required** for the application to run:

| Variable | Description | Development Default | Production Required |
|----------|-------------|---------------------|-------------------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Auto-generated | ✅ Yes |
| `DEBUG` | Enable debug mode | `True` | `False` |
| `DJANGO_SETTINGS_MODULE` | Django settings module to use | `config.settings.development` | `config.settings.production` |
| `DB_ENGINE` | Database backend | `django.db.backends.sqlite3` | `django.db.backends.postgresql` |
| `DB_NAME` | Database name | `db.sqlite3` | `lims_db` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,*` | ✅ Yes (must include domain and IP) |

### Database Variables (Required for PostgreSQL)

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | (empty) |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

**Note**: For development, SQLite is used by default (no additional DB variables needed).

### Security Variables (Required for Production)

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of frontend origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `SECURE_SSL_REDIRECT` | Force HTTPS redirect | `True` |
| `SECURE_HSTS_SECONDS` | HSTS header duration | `31536000` (1 year) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL for caching | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker URL | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://localhost:6379/0` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token lifetime | `7` |
| `EMAIL_HOST` | SMTP server host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_HOST_USER` | SMTP username | (empty) |
| `EMAIL_HOST_PASSWORD` | SMTP password | (empty) |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@{SERVER_NAME}` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SERVER_NAME` | Server domain name | (empty) |

## Frontend Environment Variables

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `/api/v1/` |

**Note**: The frontend `.env` file is automatically created by `setup.sh` for development.

## Environment Setup

### Development Setup

The `setup.sh` script automatically:
1. Generates a secure `SECRET_KEY`
2. Creates `.env` file with SQLite configuration
3. Sets `DEBUG=True`
4. Configures development settings

**No manual configuration needed!**

### Production Setup

For production, you **must** set these variables:

```bash
# Critical security variables
SECRET_KEY=<generate-with-python3-c-import-secrets-print-secrets-token-urlsafe-50>
DB_PASSWORD=<generate-secure-password>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=<your-secure-password>
DB_HOST=db
DB_PORT=5432

# Settings
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
```

### Generating Secure Values

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Generate DB_PASSWORD:**
```bash
openssl rand -base64 32
```

## Docker Compose

When using Docker Compose, environment variables can be set in:
1. `.env` file in the project root (for docker-compose)
2. `lims-backend/.env` file (for Django)
3. `frontend/.env` file (for Vite)

See `docker-compose.yml` for production environment variable configuration.

## File Locations

- **Backend `.env`**: `lims-backend/.env`
- **Frontend `.env`**: `frontend/.env`
- **Example file**: `lims-backend/.env.example`

## Security Notes

⚠️ **Never commit `.env` files to version control!**

- `.env` files are in `.gitignore`
- Use `.env.example` as a template
- Generate new `SECRET_KEY` for each environment
- Use strong passwords for production databases
- Restrict `ALLOWED_HOSTS` in production
- Use HTTPS in production (`SECURE_SSL_REDIRECT=True`)

## Troubleshooting

### "SECRET_KEY not set" error
- Ensure `.env` file exists in `lims-backend/`
- Check that `SECRET_KEY` is set in the file
- Run `setup.sh` to auto-generate

### "ALLOWED_HOSTS" error in production
- Set `ALLOWED_HOSTS` to include your domain and server IP
- Format: `domain.com,www.domain.com,xxx.xxx.xxx.xxx`

### Database connection errors
- Verify database is running
- Check `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
- For PostgreSQL, ensure database exists: `CREATE DATABASE lims_db;`

### CORS errors
- Set `CORS_ALLOWED_ORIGINS` to match your frontend URL
- Include protocol: `http://` or `https://`
- No trailing slashes

## See Also

- `setup.sh` - Automated setup script
- `lims-backend/.env.example` - Example environment file
- `docker-compose.yml` - Docker environment configuration
- `README.md` - General setup instructions

