.PHONY: help up down build restart logs shell dbshell \
       migrate makemigrations superuser check collectstatic \
       lint lint-fix format format-check typecheck \
       test test-cov \
       celery-worker celery-beat celery-logs \
       clean flush reset-db

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
DC    := docker compose
EXEC  := $(DC) exec web
MANAGE := $(EXEC) python manage.py

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ──────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────
up: ## Start all services in background
	$(DC) up -d

down: ## Stop all services
	$(DC) down

build: ## Build/rebuild containers
	$(DC) up --build -d

restart: ## Restart all services
	$(DC) restart

logs: ## Tail all container logs
	$(DC) logs -f

logs-web: ## Tail web container logs
	$(DC) logs -f web

shell: ## Open Django shell_plus / shell
	$(MANAGE) shell

dbshell: ## Open PostgreSQL shell
	$(DC) exec db psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-whatsapp_crm}

bash: ## Open bash in web container
	$(EXEC) bash

# ──────────────────────────────────────────────
# Django
# ──────────────────────────────────────────────
migrate: ## Run migrations
	$(MANAGE) migrate

makemigrations: ## Generate migrations
	$(MANAGE) makemigrations

superuser: ## Create superuser
	$(MANAGE) createsuperuser

check: ## Run Django system checks
	$(MANAGE) check

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

showurls: ## Show all registered URL patterns
	$(MANAGE) show_urls 2>/dev/null || $(EXEC) python -c \
		"import django; django.setup(); \
		from django.urls import get_resolver; \
		[print(p.pattern) for p in get_resolver().url_patterns]"

# ──────────────────────────────────────────────
# Linting & Formatting (ruff)
# ──────────────────────────────────────────────
lint: ## Run ruff linter (check only)
	$(EXEC) ruff check .

lint-fix: ## Run ruff linter and auto-fix
	$(EXEC) ruff check . --fix

format: ## Format code with ruff
	$(EXEC) ruff format .

format-check: ## Check formatting without changes
	$(EXEC) ruff format . --check

# ──────────────────────────────────────────────
# Pylint
# ──────────────────────────────────────────────
pylint: ## Run pylint on all apps
	$(EXEC) pylint apps/ core/ infrastructure/

# ──────────────────────────────────────────────
# Type checking
# ──────────────────────────────────────────────
typecheck: ## Run mypy type checker
	$(EXEC) mypy apps/ core/ infrastructure/

# ──────────────────────────────────────────────
# All quality checks
# ──────────────────────────────────────────────
qa: lint format-check typecheck check ## Run all quality checks

fix: lint-fix format ## Auto-fix lint + format

# ──────────────────────────────────────────────
# Testing
# ──────────────────────────────────────────────
test: ## Run tests
	$(EXEC) pytest

test-cov: ## Run tests with coverage report
	$(EXEC) pytest --cov=apps --cov-report=term-missing

# ──────────────────────────────────────────────
# Celery
# ──────────────────────────────────────────────
celery-worker: ## Start celery worker (foreground)
	$(DC) up celery-worker

celery-beat: ## Start celery beat (foreground)
	$(DC) up celery-beat

celery-logs: ## Tail celery worker logs
	$(DC) logs -f celery-worker celery-beat

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
flush: ## Flush all data (keep tables)
	$(MANAGE) flush --noinput

reset-db: ## Drop & recreate database + migrate
	$(DC) exec db psql -U $${POSTGRES_USER:-postgres} -c "DROP DATABASE IF EXISTS $${POSTGRES_DB:-whatsapp_crm};"
	$(DC) exec db psql -U $${POSTGRES_USER:-postgres} -c "CREATE DATABASE $${POSTGRES_DB:-whatsapp_crm};"
	$(MANAGE) migrate
	@echo "Database reset complete."

reset-migrations: ## Delete all migration files and regenerate
	$(EXEC) find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
	$(MANAGE) makemigrations main_crm chatbot_builder conversation messaging
	@echo "Migrations regenerated."

# ──────────────────────────────────────────────
# Cleanup
# ──────────────────────────────────────────────
clean: ## Remove __pycache__, .pyc, .pyo files
	$(EXEC) find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	$(EXEC) find . -name "*.pyc" -o -name "*.pyo" | xargs rm -f 2>/dev/null; true
	@echo "Cleaned."
