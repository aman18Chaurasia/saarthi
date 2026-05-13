.PHONY: up down migrate api web test lint setup seed seed-clear

COMPOSE = docker compose -f infra/docker-compose.yml

## setup: install all deps (en_core_web_lg is a pinned dep — no separate download needed)
setup:
	uv sync --all-packages
	pnpm install

## up: start all backing services (Postgres, Redis, Qdrant, Neo4j, MinIO)
up:
	$(COMPOSE) up -d

## down: stop all backing services
down:
	$(COMPOSE) down

## migrate: run database migrations
migrate:
	cd apps/api && uv run alembic upgrade head

## api: run FastAPI dev server on :8000
api:
	uv run uvicorn apps.api.main:app --reload --port 8000

## web: run Next.js dev server on :3000
web:
	pnpm --filter web dev

## test: run pytest + vitest
test:
	uv run pytest -q
	pnpm --filter web test --run

## lint: ruff + mypy + biome
lint:
	uv run ruff check .
	uv run mypy .
	pnpm --filter web exec biome check .

## seed: populate database with test call data
seed:
	uv run python apps/api/seed_data.py

## seed-clear: clear all calls from database
seed-clear:
	uv run python apps/api/seed_data.py --clear
