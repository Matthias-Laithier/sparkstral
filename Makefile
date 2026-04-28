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
	cd sparkstral && uv run ruff format . && uv run ruff check --select I --fix

lint:
	cd sparkstral && uv run ruff check .

typecheck:
	cd sparkstral && uv run mypy src

test:
	cd sparkstral && uv run pytest

check: format lint typecheck test
