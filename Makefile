.PHONY: help setup dev-backend dev-frontend generate-types docker-up docker-down docker-logs migrate lint test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies
	@echo "Installing backend dependencies with uv..."
	cd app/backend && uv sync --extra dev
	@echo "Installing frontend dependencies with pnpm..."
	cd app/frontend && pnpm install
	@echo "Creating symlink for Docker Compose .env..."
	ln -sf ../.env infrastructure/.env
	@echo "Setup complete!"

generate-types: ## Generate TypeScript types from OpenAPI spec
	@./scripts/generate-types.sh

dev-backend: ## Run backend locally
	cd app/backend && python run.py

dev-frontend: ## Run frontend locally
	cd app/frontend && pnpm dev

docker-build: ## Build Docker images
	docker compose -f infrastructure/docker-compose.yml build

docker-up: ## Start Docker Compose services
	docker compose -f infrastructure/docker-compose.yml up -d

docker-down: ## Stop Docker Compose services
	docker compose -f infrastructure/docker-compose.yml down

docker-logs: ## Show Docker Compose logs
	docker compose -f infrastructure/docker-compose.yml logs -f

docker-restart: ## Restart Docker Compose services
	docker compose -f infrastructure/docker-compose.yml restart

docker-migrate: ## Run migrations in Docker container
	docker compose -f infrastructure/docker-compose.yml exec backend alembic upgrade head

docker-migrate-create: ## Create new migration in Docker (use MESSAGE="description")
	docker compose -f infrastructure/docker-compose.yml exec backend alembic revision --autogenerate -m "$(MESSAGE)"

migrate: ## Run database migrations
	cd app/backend && alembic upgrade head

migrate-create: ## Create new migration (use MESSAGE="description")
	cd app/backend && alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Rollback last migration
	cd app/backend && alembic downgrade -1

lint: ## Run linting and formatting checks
	cd app/backend && black --check src tests --line-length 100
	cd app/backend && ruff check src tests
	cd app/backend && mypy src

lint-fix: ## Fix linting issues
	cd app/backend && black src tests --line-length 100
	cd app/backend && ruff check --fix src tests

test: ## Run tests
	cd app/backend && pytest -v

test-cov: ## Run tests with coverage
	cd app/backend && pytest --cov=src --cov-report=html --cov-report=term

clean: ## Clean cache and artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf app/backend/htmlcov
	@echo "Cleanup complete!"
