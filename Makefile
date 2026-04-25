.PHONY: up down logs build ps restart clean format lint typecheck test check

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

ps:
	docker compose ps

restart:
	docker compose restart

clean:
	docker compose down -v --remove-orphans

format:
	cd backend && uv run ruff format . && uv run ruff check --select I --fix
	cd workflow_worker && uv run ruff format . && uv run ruff check --select I --fix
	cd frontend && npm run format

lint:
	cd backend && uv run ruff check .
	cd workflow_worker && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy src
	cd workflow_worker && uv run mypy src
	cd frontend && npm run typecheck

test:
	cd backend && uv run pytest
	cd workflow_worker && uv run pytest
	cd frontend && npm run test

check: format lint typecheck test
