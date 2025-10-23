    .PHONY: help install dev docker-build docker-up docker-down docker-logs docker-restart \
	lint-frontend lint-frontend-fix lint lint-fix test-frontend test test-cov generate-types clean

    help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

    install: ## Install frontend dependencies
	cd app/frontend && pnpm install

    dev: ## Start Next.js dev server
	cd app/frontend && pnpm dev

    docker-build: ## Build Docker image
	docker compose -f infrastructure/docker-compose.yml build

    docker-up: ## Start Docker Compose services
	docker compose -f infrastructure/docker-compose.yml up -d

    docker-down: ## Stop Docker Compose services
	docker compose -f infrastructure/docker-compose.yml down

    docker-logs: ## Show Docker Compose logs
	docker compose -f infrastructure/docker-compose.yml logs -f

    docker-restart: ## Restart Docker Compose services
	docker compose -f infrastructure/docker-compose.yml restart

    lint: ## Run linting and type-checks
	@echo "Linting frontend..."
	cd app/frontend && pnpm lint:check
	cd app/frontend && pnpm type-check

    lint-fix: ## Fix lint issues
	@echo "Fixing frontend lint issues..."
	cd app/frontend && pnpm lint:fix

    test: ## Run frontend tests
	cd app/frontend && pnpm test

    test-cov: ## Run frontend tests with coverage
	@echo "Running frontend tests with coverage..."
	cd app/frontend && pnpm test:coverage

    generate-types: ## Generate TypeScript types from OpenAPI spec
	@./scripts/generate-types.sh

    clean: ## Clean frontend artifacts
	@echo "Cleaning frontend..."
	rm -rf app/frontend/.next
	rm -rf app/frontend/out
	rm -rf app/frontend/coverage
	@echo "Cleanup complete!"
