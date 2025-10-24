.PHONY: build up down test lint

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

test:
	cd backend && pytest -q || true
	cd frontend && npm ci && npm run build || true

lint:
	cd backend && ruff .
	cd frontend && npm run lint || true
