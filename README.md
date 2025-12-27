# Laboratory Information Management System (LIMS)

A comprehensive, production-ready Laboratory Information Management System built with Django 5, Django REST Framework, PostgreSQL, Celery, Redis, React, and TypeScript.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Development Setup](#development-setup)
  - [Docker Setup](#docker-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🔬 Overview

This LIMS is a complete software solution designed to manage all activities in a medium-scale routine laboratory. It digitalizes the workflow from patient registration to report generation, replacing paper-based processes with a faster, more accurate, and easier-to-manage system.

### Target Users

- **Reception Staff** - Patient registration and order creation
- **Cashier/Billing Staff** - Payment processing and receipt generation
- **Phlebotomist/Sample Collector** - Sample collection tracking
- **Lab Technician** - Test result entry
- **Pathologist/Lab Director** - Result verification and report authorization
- **System Administrator** - System management and configuration
- **Manager/Supervisor** - Operations oversight and reporting

## ✨ Features

### Core Features (Phase 1)

- ✅ **User Management** - Role-based authentication and authorization
- ✅ **Patient Management** - Complete demographic information and history
- ✅ **Order Management** - Test and panel ordering with automatic pricing
- ✅ **Sample Collection** - Barcode tracking and collection workflow
- ✅ **Result Entry** - Validation, auto-flagging, and quality controls
- ✅ **Result Verification** - Pathologist review and approval workflow
- ✅ **Report Generation** - Professional PDF reports with digital signatures
- ✅ **Billing & Payments** - Multiple payment methods and receipt generation
- ✅ **Dashboard** - Role-based statistics and metrics
- ✅ **Audit Trail** - Complete activity logging

### Test Catalog

The system comes pre-configured with a comprehensive test catalog including:

- **Hematology** - CBC, ESR, Coagulation studies
- **Clinical Chemistry** - Liver function, Kidney function, Lipid profile
- **Immunology** - Thyroid tests, Hormones
- **Microbiology** - Culture and sensitivity tests
- **Tumor Markers** - Various cancer markers

See [TEST_CATALOG_EXPANDED.md](./TEST_CATALOG_EXPANDED.md) for complete test details.

## 🛠 Technology Stack

### Backend

- **Framework**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL 16+
- **Cache & Queue**: Redis 7+
- **Task Queue**: Celery
- **Authentication**: JWT (djangorestframework-simplejwt)
- **PDF Generation**: ReportLab
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)

### Frontend

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Styling**: CSS Modules

### Infrastructure

- **Web Server**: Caddy (reverse proxy)
- **Application Server**: Gunicorn
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│                  Client (Browser)                │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────────────┐
│            Caddy Reverse Proxy                   │
│  - Frontend (React) serving                      │
│  - Backend API proxying                          │
│  - Static & Media file serving                   │
└──┬─────────────────────────────────────────┬────┘
   │                                         │
   │ /api/*, /admin/*                        │ /*
   │                                         │
┌──▼─────────────────────┐    ┌─────────────▼────┐
│  Django Backend         │    │   React Frontend │
│  - REST API             │    │   - SPA          │
│  - Admin Interface      │    │   - PWA Ready    │
│  - Background Tasks     │    └──────────────────┘
└──┬──────────┬───────────┘
   │          │
   │          │
┌──▼──────┐ ┌▼──────────┐
│PostgreSQL│ │Redis      │
│Database  │ │Cache/Queue│
└──────────┘ └───────────┘
```

For detailed architecture, see [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md).

## 🚀 Getting Started

### Prerequisites

#### For Development (Bare Metal)

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+

#### For Docker Deployment

- Docker 24+
- Docker Compose 2.20+

### Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/munaimtahir/lims.git
cd lims
```

#### 2. Backend Setup

```bash
cd lims-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Copy environment file
cp .env.example .env

# Update .env with your database credentials
# DB_NAME=lims_db
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py loaddata sample_data.json

# Run development server
python manage.py runserver
```

The backend will be available at `http://localhost:8000`
- API Root: `http://localhost:8000/api/`
- Admin Panel: `http://localhost:8000/admin/`
- API Documentation: `http://localhost:8000/api/docs/`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Update .env with backend URL
# VITE_API_BASE_URL=http://localhost:8000

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### 4. Run Celery Worker (Optional)

For background tasks like PDF generation:

```bash
cd lims-backend
celery -A config worker -l INFO
```

### Docker Setup

#### 1. Prepare Environment

```bash
# Create .env file in root directory
cp .env.example .env

# Update environment variables
nano .env
```

Required environment variables:
```env
SECRET_KEY=your-secret-key-here-change-in-production
DB_PASSWORD=secure_database_password
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

#### 2. Build and Run

```bash
# Build images
docker-compose build

# Run all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# (Optional) Load sample data
docker-compose exec backend python manage.py loaddata sample_data.json
```

#### 3. Access the Application

- Application: `http://localhost`
- Admin Panel: `http://localhost/admin/`
- API Documentation: `http://localhost/api/docs/`

#### 4. Stop Services

```bash
docker-compose down
```

To remove volumes (database data):
```bash
docker-compose down -v
```

## 📁 Project Structure

```
lims/
├── lims-backend/              # Django backend
│   ├── apps/                  # Django applications
│   │   ├── accounts/          # User management & authentication
│   │   ├── patients/          # Patient management
│   │   ├── laboratory/        # Test catalog (tests, panels, categories)
│   │   ├── orders/            # Order management
│   │   ├── samples/           # Sample collection tracking
│   │   ├── results/           # Result entry & verification
│   │   ├── reports/           # Report generation
│   │   ├── billing/           # Payment & billing
│   │   ├── audit/             # Audit trail
│   │   └── dashboard/         # Dashboard statistics
│   ├── config/                # Project configuration
│   │   ├── settings/          # Settings (base, dev, prod)
│   │   ├── urls.py            # URL routing
│   │   └── wsgi.py            # WSGI entry point
│   ├── requirements/          # Python dependencies
│   ├── manage.py              # Django CLI
│   └── Dockerfile             # Backend container
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── api/               # API client & services
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── contexts/          # React contexts (Auth, etc.)
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx            # Main app component
│   ├── public/                # Static assets
│   ├── package.json           # npm dependencies
│   ├── vite.config.ts         # Vite configuration
│   └── Dockerfile             # Frontend container
│
├── docs/                      # Documentation
│   ├── architecture/          # Architecture documentation
│   │   └── ARCHITECTURE.md
│   ├── api/                   # API documentation
│   │   └── API_DESIGN.md
│   ├── deployment/            # Deployment guides
│   │   ├── DEPLOYMENT.md
│   │   ├── SSH_DEPLOYMENT.md
│   │   └── TROUBLESHOOTING.md
│   ├── archive/               # Archived documentation
│   ├── DATA_MODEL.md          # Database schema
│   ├── WORKFLOW.md            # Laboratory workflows
│   ├── VISION.md              # Project vision & goals
│   ├── TEST_CATALOG_EXPANDED.md # Complete test catalog
│   └── LEGACY_LAB.md          # Legacy code reference guide
│
├── archive/                   # Archived code and documentation
│   └── legacy_lab/            # Legacy code reference (read-only)
│       └── lab-main/          # Old LIMS for data migration reference
│
├── scripts/                    # Utility scripts
│   ├── deploy.sh              # Deployment script
│   ├── health-check.sh        # Health monitoring script
│   └── validate_system.sh     # System validation script
│
├── .github/workflows/         # CI/CD pipelines
├── docker-compose.yml         # Docker orchestration
├── Caddyfile                  # Reverse proxy configuration
├── CHANGELOG.md               # Version history
├── LICENSE                    # License file
└── README.md                  # This file
```

## 🧪 Running Tests

### Backend Tests

```bash
cd lims-backend

# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report
coverage html  # Generate HTML report

# Run specific test file
pytest apps/patients/tests/test_patients.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run linting
npm run lint

# Run type checking
npm run type-check

# Build (validates TypeScript)
npm run build
```

### CI/CD

The project includes GitHub Actions workflows for:
- Backend testing (pytest with coverage)
- Frontend linting and build
- Docker image building

See `.github/workflows/ci.yml` for details.

## 📚 Documentation

### Design Documents

- [VISION.md](./docs/VISION.md) - Project vision, goals, and core values
- [ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md) - Complete system architecture
- [API_DESIGN.md](./docs/api/API_DESIGN.md) - RESTful API specification
- [DATA_MODEL.md](./docs/DATA_MODEL.md) - Database schema and relationships
- [WORKFLOW.md](./docs/WORKFLOW.md) - Laboratory workflows and business logic

### Deployment

- [DEPLOYMENT.md](./docs/deployment/DEPLOYMENT.md) - Production deployment guide
- [SSH_DEPLOYMENT.md](./docs/deployment/SSH_DEPLOYMENT.md) - SSH deployment instructions
- [TROUBLESHOOTING.md](./docs/deployment/TROUBLESHOOTING.md) - Troubleshooting guide

### Reference

- [TEST_CATALOG_EXPANDED.md](./docs/TEST_CATALOG_EXPANDED.md) - Complete test catalog
- [LEGACY_LAB.md](./docs/LEGACY_LAB.md) - Legacy code reference guide
- [CHANGELOG.md](./CHANGELOG.md) - Version history

### Archived Documentation

Historical and redundant documentation is archived in [`docs/archive/`](./docs/archive/).

### API Documentation

- Interactive API docs (Swagger UI): `http://localhost:8000/api/docs/`
- ReDoc format: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## 🔐 Security

- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC) for all endpoints
- HTTPS/TLS encryption in production
- SQL injection prevention via Django ORM
- XSS protection via React escaping
- CORS configuration for frontend domain
- Audit logging for all critical operations
- Password hashing with bcrypt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Backend: Follow PEP 8, use `black` for formatting, `flake8` for linting
- Frontend: ESLint with TypeScript rules, Prettier for formatting

### Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Maintain or improve code coverage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django and Django REST Framework communities
- React and TypeScript ecosystems
- All contributors and maintainers

## 📞 Support

For issues, questions, or contributions:
- GitHub Issues: [https://github.com/munaimtahir/lims/issues](https://github.com/munaimtahir/lims/issues)
- Project Wiki: [https://github.com/munaimtahir/lims/wiki](https://github.com/munaimtahir/lims/wiki)

---

**Note**: This is a production-grade LIMS system. For legacy code reference and data migration, see [`archive/legacy_lab/`](./archive/legacy_lab/) directory. The legacy code is preserved for reference only and should not be run as a separate application. See [`docs/LEGACY_LAB.md`](./docs/LEGACY_LAB.md) for more information.

Made with ❤️ for modern laboratories
