SETTINGS_PATH ?= ./pyproject.toml
PORT ?= 8000
GIT_ARGS := --name-only --diff-filter=d --cached
ifneq ($(DIFF_SRC),)
	GIT_ARGS := --name-only --diff-filter=d $(DIFF_SRC)...HEAD
endif

DIFF_FILES = `git diff $(GIT_ARGS)`
DIFF_PYTHONS = `git diff $(GIT_ARGS) | grep .py$$`


format:
	@if [[ ! -z "${DIFF_PYTHONS}" ]]; then \
		echo "> autoflake"; autoflake --remove-all-unused-imports --ignore-init-module-imports -r -i $(DIFF_FILES); \
		echo "> black"; black --config $(SETTINGS_PATH) -q $(DIFF_PYTHONS); \
	fi

lint:
	@if command -v cspell > /dev/null; then \
		echo "> cspell"; cspell --gitignore --no-progress --no-summary --no-must-find-files $(DIFF_FILES); \
	fi;
	@if [[ ! -z "$(DIFF_PYTHONS)" ]]; then \
		echo "> pylint"; pylint --rcfile=$(SETTINGS_PATH) -sn $(DIFF_PYTHONS); \
		echo "> ruff"; ruff check $(DIFF_PYTHONS); \
		echo "> pyright"; pyright $(DIFF_PYTHONS); \
	fi

test:
	@echo "Running comprehensive test suite..."
	@coverage erase
	@echo "Running multi-database compatibility tests..."
	@bats --timing ./tests/api_db_test.bats
	@echo "Running AI Agent specific tests..."
	@make test-ai-agent
	@coverage report --show-missing --skip-covered --fail-under 90
	@coverage html

up:
	uvicorn main:app \
		--port $(PORT) \
		--app-dir ./src \
		--reload

db:
	docker compose down --remove-orphans -v
	docker compose up dockerize

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t homunculy:latest .

docker-up:
	@echo "Starting services with Docker Compose..."
	docker compose up -d

docker-down:
	@echo "Stopping services..."
	docker compose down

docker-logs:
	@echo "Showing logs..."
	docker compose logs -f homunculy-app

docker-restart:
	@echo "Restarting application..."
	docker compose restart homunculy-app

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker compose down -v --remove-orphans
	docker system prune -f

docker-shell:
	@echo "Opening shell in application container..."
	docker compose exec homunculy-app /bin/bash

# Root docker-compose commands (all services)
docker-up-all:
	@echo "Starting all services from root..."
	cd .. && docker compose up -d

docker-down-all:
	@echo "Stopping all services from root..."
	cd .. && docker compose down

docker-logs-all:
	@echo "Showing all service logs..."
	cd .. && docker compose logs -f
