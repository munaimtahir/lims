# Setup Instructions

This mono-repo contains backend and frontend applications with complete testing infrastructure.

## Initial Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Backend Setup (Django)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

### Frontend Setup (Vite + React + TypeScript)

```bash
cd frontend
npm install
```

### Pre-commit Hooks (Optional but Recommended)

```bash
# From the repository root
pip install pre-commit
pre-commit install
```

## Running the Applications

### Backend Development Server

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

The backend will be available at http://localhost:8000
- Health check endpoint: http://localhost:8000/health/

### Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest                    # Run tests
pytest -v                 # Run tests with verbose output
pytest --cov=.           # Run tests with coverage report
```

Current coverage: 100% (27 statements)

### Frontend Tests

```bash
cd frontend
npm test                  # Run unit tests (watch mode)
npm run test:coverage     # Run tests with coverage report
npm run playwright        # Run Playwright e2e tests (requires browser installation)
```

Current coverage: 100%

## Code Quality

### Backend Linting and Formatting

```bash
cd backend
source venv/bin/activate
black .                   # Format code
isort .                   # Sort imports
ruff check .              # Lint code
ruff check --fix .        # Lint and auto-fix
mypy .                    # Type check
```

### Frontend Linting and Formatting

```bash
cd frontend
npm run format            # Format code with Prettier
npm run format:check      # Check formatting
npm run lint              # Run ESLint
```

## Project Structure

```
lab/
├── backend/              # Django API
│   ├── core/            # Django project settings
│   ├── health/          # Health check app
│   ├── pyproject.toml   # Tool configurations
│   ├── pytest.ini       # Pytest configuration
│   └── requirements.txt # Python dependencies
├── frontend/            # Vite + React + TypeScript
│   ├── src/             # Source code
│   ├── e2e/             # Playwright tests
│   ├── vite.config.ts   # Vite and Vitest configuration
│   └── package.json     # NPM dependencies and scripts
├── infra/               # Infrastructure configs
├── docs/                # Documentation
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Dependencies

### Backend
- Django 5.2.7
- pytest, pytest-django, pytest-cov
- factory_boy (test fixtures)
- freezegun (time mocking)
- ruff (linter)
- mypy (type checker)
- black (formatter)
- isort (import sorter)
- django-stubs (Django type hints)

### Frontend
- Vite 7.1.7
- React 19.1.1
- TypeScript 5.9.3
- Vitest 4.0.6 (unit testing)
- @testing-library/react (testing utilities)
- Playwright 1.56.1 (e2e testing)
- ESLint 9.39.0
- Prettier 3.6.2

## Next Steps

1. Set up database (PostgreSQL recommended for production)
2. Configure environment variables
3. Add CI/CD pipelines in `infra/`
4. Add comprehensive documentation in `docs/`
5. Implement additional features and tests
