# LIMS Scaffold

This repository contains the initial scaffold for a Laboratory Information Management System (LIMS) featuring a FastAPI backend, Next.js frontend, and PostgreSQL database orchestrated via Docker Compose.

## Getting Started

1. Build and start services:
   ```bash
   docker compose up -d --build
   ```
2. Verify the stack:
   - API health: http://localhost:8000/health should respond with `{ "status": "ok" }`
   - Frontend dashboard: http://localhost:3000 should display **"LIMS — Demo Dashboard"**
3. Stop the services:
   ```bash
   docker compose down
   ```

## Project Structure
```
backend/              # FastAPI backend application
  app/                # Application code
    models/           # Database models
    routers/          # API endpoints
    main.py           # Application entry point
    database.py       # Database configuration
  tests/              # Backend tests
  requirements.txt    # Python dependencies
  pyproject.toml      # Python tooling configuration
  Dockerfile          # Backend container configuration
  .env.example        # Environment variables template

frontend/             # Next.js frontend application
  pages/              # Next.js pages
  package.json        # Node.js dependencies
  tsconfig.json       # TypeScript configuration
  .eslintrc.json      # ESLint configuration
  .prettierrc.json    # Prettier configuration
  Dockerfile          # Frontend container configuration
  .env.example        # Environment variables template

data/                 # Reference data files
  reference_ranges.csv
  critical_values.csv
  delta_rules.csv

docs/                 # Documentation
  Setup.md
  OpenAPI.md
  CONTRIBUTING.md
  CODING_STANDARDS.md

.github/workflows/    # CI/CD workflows
  ci.yml

docker-compose.yml    # Docker Compose orchestration
Makefile              # Build automation
.env.example          # Root environment variables template
```

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linters and type checker
ruff check .              # Lint code
black .                   # Format code
mypy .                    # Type check

# Run tests
pytest -q                 # Run all tests
pytest -v                 # Run tests with verbose output
pytest --cov              # Run tests with coverage
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run linters and type checker
npm run lint              # Lint code
npm run format            # Format code
npm run type-check        # Type check TypeScript

# Run development server
npm run dev               # Start dev server at http://localhost:3000

# Build for production
npm run build
npm start
```

### Environment Variables

Copy the `.env.example` file to `.env` in the respective directories and adjust values as needed:

```bash
# Root level
cp .env.example .env

# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

## Next Steps
Proceed to Stage A: Foundation & Setup to continue feature development.
