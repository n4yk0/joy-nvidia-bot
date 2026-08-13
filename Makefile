.PHONY: install test lint run dry test-msg status docker up down logs

install:
	uv sync

test:
	uv run pytest -q

lint:
	uv run ruff check .

run:
	uv run joy-bot

dry:
	STATE_FILE=./data/state.json DRY_RUN=true uv run joy-bot

test-msg:
	uv run joy-bot test

status:
	uv run joy-bot status

docker:
	docker build -t joy-bot:latest .

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100
