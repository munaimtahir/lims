# Laboratory Information Management System (LIMS) - Backend

This repository contains the backend API for the Laboratory Information Management System (LIMS), built with Django and Django REST Framework.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Development](#development)
- [Database](#database)
- [Project Status](#project-status)
- [Next Steps](#next-steps)

## Overview

The LIMS backend provides a robust and scalable API for managing laboratory operations, including patient management, test ordering, sample tracking, result entry, and reporting.

## Features

- **User Management**: Role-based access control for different user types.
- **Patient Management**: Create, retrieve, update, and search for patient records.
- **Test Catalog**: Manage laboratory tests, panels, and categories.
- **Order Management**: Place and track orders for patients.
- **Sample Collection**: Track the collection and status of samples.
- **Result Entry**: Enter and verify test results.
- **Billing**: Manage payments for orders.
- **Reporting**: Generate PDF reports for orders.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or SQLite for development)
- Redis 7+ (for caching and Celery)

## Quick Start

1.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements/development.txt
    ```

3.  **Configure Environment**
    ```bash
    cp .env.example .env
    # Edit .env with your database credentials
    ```

4.  **Run Migrations**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run Development Server**
    ```bash
    python manage.py runserver
    ```

7.  **Access Application**
    - API: http://127.0.0.1:8000/api/v1/
    - Admin: http://127.0.0.1:8000/admin/
    - API Docs: http://127.0.0.1:8000/api/docs/

## Project Structure

```
lims-backend/
├── apps/                    # Django applications
│   ├── accounts/           # User management & auth
│   ├── patients/           # Patient management
│   ├── laboratory/         # Test catalog
│   ├── orders/             # Order management
│   ├── samples/            # Sample collection
│   ├── results/            # Result entry
│   ├── reports/            # PDF reports
│   ├── billing/            # Payments
│   └── audit/              # Audit trail
├── config/                 # Project configuration
│   ├── settings/          # Settings modules
│   ├── urls.py            # Root URL config
│   └── wsgi.py            # WSGI config
├── requirements/          # Dependencies
├── manage.py             # Django management script
└── .env                  # Environment variables
```

## API Endpoints

A comprehensive list of API endpoints is available in the API documentation, which can be accessed at `http://127.0.0.1:8000/api/docs/` when the development server is running.

## User Roles

1.  **Admin**: Full access to all system features.
2.  **Receptionist**: Manages patients and orders.
3.  **Cashier**: Manages payments and billing.
4.  **Phlebotomist**: Manages sample collection.
5.  **Lab Technician**: Enters test results.
6.  **Pathologist**: Verifies and rejects test results.
7.  **Manager**: Views reports and manages laboratory operations.

## Development

**Run Tests**
```bash
pytest
```

**Code Formatting**
```bash
black .
isort .
flake8
```

**Make Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

## Database

**Using SQLite (Development)**
Set in .env:
```
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

**Using PostgreSQL (Production)**
Set in .env:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## Project Status

✅ Project structure set up
✅ User authentication with JWT
✅ Patient management
✅ Test catalog models
✅ Order management
✅ Sample collection
✅ Result entry
✅ PDF report generation
✅ Billing & payments

## Next Steps

1.  Build out all API endpoints
2.  Add comprehensive testing
3.  Set up Celery for background tasks
4.  Build React frontend
5.  Deploy to VPS
