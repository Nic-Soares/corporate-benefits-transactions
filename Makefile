# Shortcuts for the pipeline. `make help` lists them.
# make dataset SCALE=4 DAYS=365 TODAY=2026-09-01 SEED=42

SEED  ?= 42
TODAY ?= 2026-09-01
DAYS  ?= 365
SCALE ?= 1
RUN   := uv run benefits
# Keep a Mac awake through a long run (a no-op elsewhere)
AWAKE := $(shell command -v caffeinate >/dev/null && echo caffeinate -i)

.PHONY: help install db db-stop db-wipe check test test-db dataset clean

help: ## This list
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

install: ## Dependencies from uv.lock
	uv sync

db: ## Start Postgres and wait until it is ready
	docker compose up -d --wait

db-stop: ## Stop Postgres (the data stays)
	docker compose stop

db-wipe: ## Stop Postgres and delete its data
	docker compose down -v

check: ## Lint, format and the offline tests (what CI runs first)
	uv run ruff check
	uv run ruff format --check
	uv run pytest

test-db: db ## The tests that need Postgres
	uv run pytest -m db

dataset: db ## The whole pipeline: setup, simulate, etl, export
	$(AWAKE) $(RUN) setup --seed $(SEED) --today $(TODAY) --scale $(SCALE) --reset
	$(AWAKE) $(RUN) simulate --seed $(SEED) --today $(TODAY) --days $(DAYS)
	$(AWAKE) $(RUN) etl
	$(RUN) export

clean: ## Delete the generated OLAP file and dataset (data/raw stays)
	find data/olap data/dataset -type f ! -name .gitkeep -delete
