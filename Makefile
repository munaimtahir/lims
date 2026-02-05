.PHONY: up build restart stop logs down down_hard check_volume backup

up:
	docker compose up -d

build:
	docker compose up -d --build

restart:
	docker compose restart

stop:
	docker compose stop

logs:
	docker compose logs -f --tail=200

down:
	docker compose down

down_hard:
	@echo "⚠️  DANGER: This will DELETE the database volume."
	@echo "Type YES_DELETE_DB to continue:"; read ans; \
	if [ "$$ans" = "YES_DELETE_DB" ]; then docker compose down -v; else echo "Cancelled"; fi

check_volume:
	./scripts/check_db_volume.sh

backup:
	./scripts/backup_db.sh
