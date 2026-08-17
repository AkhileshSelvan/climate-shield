# ClimateShield — developer commands
# Offline-first: every target except `fixtures-live` runs without a network.

PY      ?= .venv/bin/python
PIP     ?= .venv/bin/pip
BACKEND := backend

.PHONY: help venv install migrate dev seed seed-demo demo-reset demo-offline test fixtures fixtures-live db-up db-down clean

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

venv: ## Create the virtualenv
	python3 -m venv .venv

install: venv ## Install backend dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r $(BACKEND)/requirements.txt

db-up: ## Start local PostgreSQL (matches the deployment target)
	docker compose up -d db

db-down: ## Stop local PostgreSQL
	docker compose down

migrate: ## Apply database migrations
	cd $(BACKEND) && ../$(PY) -m alembic upgrade head

dev: ## Run the API (offline fixture provider by default)
	cd $(BACKEND) && ../$(PY) -m uvicorn app.main:app --reload --port 8000

seed: migrate ## Load weather fixtures into the cache
	cd $(BACKEND) && ../$(PY) -m seeds.seed_demo --weather-only

seed-demo: migrate ## Load fixtures plus the demo farm and policy
	cd $(BACKEND) && ../$(PY) -m seeds.seed_demo

demo-reset: ## Clear evaluations, payouts and simulated weather
	cd $(BACKEND) && ../$(PY) -m seeds.seed_demo --reset

demo-offline: seed-demo ## Full stack on fixtures — verify with the network off
	@echo "WEATHER_PROVIDER=fixture — no outbound calls on any read path."
	cd $(BACKEND) && WEATHER_PROVIDER=fixture ../$(PY) -m uvicorn app.main:app --port 8000

test: ## Run the test suite
	cd $(BACKEND) && ../$(PY) -m pytest -q

fixtures: ## Regenerate synthetic weather fixtures (offline, deterministic)
	cd $(BACKEND) && ../$(PY) seeds/generate_fixtures.py

fixtures-live: ## Refresh fixtures from Open-Meteo — the ONLY networked target
	cd $(BACKEND) && ../$(PY) seeds/generate_fixtures.py --live --years 35

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
