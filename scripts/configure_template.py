#!/usr/bin/env python3
"""
Script utilitário para adaptar o template fullstack para cenários
somente-backend ou somente-frontend.

Uso:
    python scripts/configure_template.py --mode backend
    python scripts/configure_template.py --mode frontend
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from textwrap import dedent

ROOT_DIR = Path(__file__).resolve().parent.parent


BACKEND_MAKEFILE = dedent(
    """\
    .PHONY: help setup-docker docker-build docker-up docker-down docker-logs docker-restart \\
\tdocker-migrate docker-migrate-create migrate migrate-create migrate-downgrade \\
\tlint-backend lint-backend-fix lint lint-fix test-up test-down test-backend test test-cov clean

    help: ## Show this help message
\t@echo "Available commands:"
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

    setup-docker: ## Install dependencies
\t@if [ ! -f .env ]; then \\
\t\techo "Creating .env from .env.example..."; \\
\t\tcp .env.example .env; \\
\tfi
\t@echo "Creating symlink for Docker Compose .env..."
\tln -sf ../.env infrastructure/.env
\t@echo "Setup complete!"

    docker-build: ## Build Docker images
\tdocker compose -f infrastructure/docker-compose.yml build

    docker-up: ## Start Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml up -d

    docker-down: ## Stop Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml down

    docker-logs: ## Show Docker Compose logs
\tdocker compose -f infrastructure/docker-compose.yml logs -f

    docker-restart: ## Restart Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml restart

    docker-migrate: ## Run migrations in Docker container
\tdocker compose -f infrastructure/docker-compose.yml exec backend alembic upgrade head

    docker-migrate-create: ## Create new migration in Docker (use MESSAGE="description")
\tdocker compose -f infrastructure/docker-compose.yml exec backend alembic revision --autogenerate -m "$(MESSAGE)"

    migrate: ## Run database migrations
\tcd app/backend && alembic upgrade head

    migrate-create: ## Create new migration (use MESSAGE="description")
\tcd app/backend && alembic revision --autogenerate -m "$(MESSAGE)"

    migrate-downgrade: ## Rollback last migration
\tcd app/backend && alembic downgrade -1

    lint-backend:
\tcd app/backend && black --check src tests --line-length 100
\tcd app/backend && ruff check src tests
\tcd app/backend && mypy src

    lint-backend-fix:
\tcd app/backend && black src tests --line-length 100
\tcd app/backend && ruff check --fix src tests

    lint: ## Run backend linting and type checks
\t@echo "Linting backend..."
\tcd app/backend && black --check src tests --line-length 100
\tcd app/backend && ruff check src tests
\tcd app/backend && mypy src

    lint-fix: ## Fix backend lint issues
\t@echo "Fixing backend lint issues..."
\tcd app/backend && black src tests --line-length 100
\tcd app/backend && ruff check --fix src tests

    test-up: ## Start test database (PostgreSQL)
\tdocker compose -f infrastructure/docker-compose.yml up -d postgres_test
\t@echo "Waiting for test database to be ready..."
\t@timeout 30 bash -c 'until docker compose -f infrastructure/docker-compose.yml ps postgres_test 2>/dev/null | grep -q "healthy"; do sleep 1; done' || (echo "Timeout waiting for test database" && exit 1)
\t@echo "Test database is ready!"

    test-down: ## Stop test database
\tdocker compose -f infrastructure/docker-compose.yml stop postgres_test

    test-backend: ## Run backend tests (requires test database running)
\tcd app/backend && pytest -v

    test: ## Run backend tests
\tcd app/backend && pytest -v

    test-cov: ## Run backend tests with coverage
\t@echo "Running backend tests with coverage..."
\tcd app/backend && pytest --cov=src --cov-report=html --cov-report=term

    clean: ## Clean backend cache and artifacts
\t@echo "Cleaning backend..."
\tfind . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
\tfind . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
\tfind . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
\tfind . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
\tfind . -type f -name "*.pyc" -delete 2>/dev/null || true
\trm -rf app/backend/htmlcov
\t@echo "Cleanup complete!"
    """
)


FRONTEND_MAKEFILE = dedent(
    """\
    .PHONY: help install dev docker-build docker-up docker-down docker-logs docker-restart \\
\tlint-frontend lint-frontend-fix lint lint-fix test-frontend test test-cov generate-types clean

    help: ## Show this help message
\t@echo "Available commands:"
\t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

    install: ## Install frontend dependencies
\tcd app/frontend && pnpm install

    dev: ## Start Next.js dev server
\tcd app/frontend && pnpm dev

    docker-build: ## Build Docker image
\tdocker compose -f infrastructure/docker-compose.yml build

    docker-up: ## Start Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml up -d

    docker-down: ## Stop Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml down

    docker-logs: ## Show Docker Compose logs
\tdocker compose -f infrastructure/docker-compose.yml logs -f

    docker-restart: ## Restart Docker Compose services
\tdocker compose -f infrastructure/docker-compose.yml restart

    lint-frontend:
\tcd app/frontend && pnpm lint:check && pnpm type-check

    lint-frontend-fix:
\tcd app/frontend && pnpm lint:fix

    lint: ## Run linting and type-checks
\t@echo "Linting frontend..."
\tcd app/frontend && pnpm lint:check
\tcd app/frontend && pnpm type-check

    lint-fix: ## Fix lint issues
\t@echo "Fixing frontend lint issues..."
\tcd app/frontend && pnpm lint:fix

    test-frontend:
\tcd app/frontend && pnpm test

    test: ## Run frontend tests
\tcd app/frontend && pnpm test

    test-cov: ## Run frontend tests with coverage
\t@echo "Running frontend tests with coverage..."
\tcd app/frontend && pnpm test:coverage

    generate-types: ## Generate TypeScript types from OpenAPI spec
\t@./scripts/generate-types.sh

    clean: ## Clean frontend artifacts
\t@echo "Cleaning frontend..."
\trm -rf app/frontend/.next
\trm -rf app/frontend/out
\trm -rf app/frontend/coverage
\t@echo "Cleanup complete!"
    """
)


BACKEND_CI = dedent(
    """\
    name: CI

    on:
      push:
        branches:
          - main
      pull_request:
        branches:
          - main

    jobs:
      lint-backend:
        name: Lint Backend
        runs-on: ubuntu-latest
        container:
          image: ghcr.io/astral-sh/uv:python3.11-bookworm

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Sync dependencies with uv
            working-directory: app/backend
            run: uv sync --extra dev

          - name: Run backend lint
            working-directory: app/backend
            run: |
              uv run black --check src tests --line-length 100
              uv run ruff check src tests
              uv run mypy src

      test-backend:
        name: Test Backend
        runs-on: ubuntu-latest
        container:
          image: ghcr.io/astral-sh/uv:python3.11-bookworm

        services:
          postgres:
            image: postgres:16-alpine
            env:
              POSTGRES_USER: test
              POSTGRES_PASSWORD: test
              POSTGRES_DB: fullstack_test
            options: >-
              --health-cmd "pg_isready -U test -d fullstack_test"
              --health-interval 5s
              --health-timeout 3s
              --health-retries 3
            ports:
              - 5432:5432

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Sync dependencies with uv
            working-directory: app/backend
            run: uv sync --extra dev

          - name: Run backend tests
            working-directory: app/backend
            env:
              DATABASE_URL: postgresql+asyncpg://test:test@postgres:5432/fullstack_test
            run: uv run pytest -v
    """
)


FRONTEND_CI = dedent(
    """\
    name: CI

    on:
      push:
        branches:
          - main
      pull_request:
        branches:
          - main

    jobs:
      lint-frontend:
        name: Lint Frontend
        runs-on: ubuntu-latest

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Setup pnpm
            uses: pnpm/action-setup@v4
            with:
              version: 10

          - name: Setup Node.js
            uses: actions/setup-node@v4
            with:
              node-version: 20
              cache: 'pnpm'
              cache-dependency-path: app/frontend/pnpm-lock.yaml

          - name: Install dependencies
            working-directory: app/frontend
            run: pnpm install --frozen-lockfile

          - name: Run ESLint
            working-directory: app/frontend
            run: pnpm lint:check

          - name: Run TypeScript check
            working-directory: app/frontend
            run: pnpm type-check

      test-frontend:
        name: Test Frontend
        runs-on: ubuntu-latest

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Setup pnpm
            uses: pnpm/action-setup@v4
            with:
              version: 10

          - name: Setup Node.js
            uses: actions/setup-node@v4
            with:
              node-version: 20
              cache: 'pnpm'
              cache-dependency-path: app/frontend/pnpm-lock.yaml

          - name: Install dependencies
            working-directory: app/frontend
            run: pnpm install --frozen-lockfile

          - name: Run frontend tests
            working-directory: app/frontend
            run: pnpm test
    """
)


BACKEND_COMPOSE = dedent(
    """\
    volumes:
      postgres_data:
      redis_data:

    networks:
      fullstack-network:
        driver: bridge

    services:
      postgres_fullstack:
        image: postgres:${COMPOSE_POSTGRES_VERSION:-16-alpine}
        container_name: fullstack-postgres
        restart: always
        environment:
          POSTGRES_USER: ${POSTGRES_USER:-postgres}
          POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
          POSTGRES_DB: ${POSTGRES_DB:-fullstack_template}
        ports:
          - ${COMPOSE_POSTGRES_PORTS:-127.0.0.1:5432}:${POSTGRES_PORT:-5432}
        volumes:
          - ${COMPOSE_POSTGRES_DATA:-postgres_data}:/var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
          interval: 10s
          timeout: 5s
          retries: 5
        networks:
          - fullstack-network

      postgres_test:
        image: postgres:16-alpine
        container_name: fullstack-postgres-test
        restart: "no"
        environment:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: fullstack_test
        ports:
          - "127.0.0.1:5433:5432"
        tmpfs:
          - /var/lib/postgresql/data
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U test -d fullstack_test"]
          interval: 5s
          timeout: 3s
          retries: 3
        networks:
          - fullstack-network

      redis_fullstack:
        image: redis:${COMPOSE_REDIS_VERSION:-7-alpine}
        container_name: fullstack-redis
        mem_limit: 5G
        restart: always
        stop_grace_period: 10s
        logging:
          options:
            max-size: 1G
            max-file: 5
            compress: "true"
        command:
          - redis-server
          - --port ${REDIS_PORT:-6379}
          - --requirepass ${REDIS_PASS}
          - --maxmemory 3072mb
          - --maxmemory-policy allkeys-lru
        environment:
          - TZ=America/Sao_Paulo
        ports:
          - ${COMPOSE_REDIS_PORTS:-127.0.0.1:6379}:${REDIS_PORT:-6379}
        volumes:
          - ${COMPOSE_REDIS_DATA:-redis_data}:/data
        healthcheck:
          test: ["CMD", "redis-cli", "-a", "${REDIS_PASS}", "ping"]
          interval: 10s
          timeout: 5s
          retries: 5
        networks:
          - fullstack-network

      backend:
        build:
          context: ..
          dockerfile: infrastructure/docker/Dockerfile.backend
        image: fullstack-backend:${COMPOSE_BACKEND_VERSION:-latest}
        container_name: fullstack-backend
        env_file:
          - ../.env
        pull_policy: never
        restart: always
        mem_limit: 10G
        stop_grace_period: 10s
        logging:
          options:
            max-size: 1G
            max-file: 5
            compress: "true"
        environment:
          - TZ=America/Sao_Paulo
        ports:
          - ${COMPOSE_BACKEND_PORTS:-8000}:${BACKEND_PORT:-8000}
        depends_on:
          postgres_fullstack:
            condition: service_healthy
          redis_fullstack:
            condition: service_healthy
        networks:
          - fullstack-network
    """
)


FRONTEND_COMPOSE = dedent(
    """\
    networks:
      frontend-network:
        driver: bridge

    services:
      frontend:
        build:
          context: ..
          dockerfile: infrastructure/docker/Dockerfile.frontend
        image: frontend-app:${COMPOSE_FRONTEND_VERSION:-latest}
        container_name: frontend-app
        pull_policy: never
        restart: always
        mem_limit: 5G
        stop_grace_period: 10s
        logging:
          options:
            max-size: 1G
            max-file: 5
            compress: "true"
        environment:
          - TZ=America/Sao_Paulo
          - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}
        ports:
          - ${COMPOSE_FRONTEND_PORTS:-3000}:3000
        networks:
          - frontend-network
    """
)


FRONTEND_LAUNCH_JSON = dedent(
    """\
    {
      "version": "0.2.0",
      "configurations": [
        {
          "name": "Frontend: Next.js Dev",
          "type": "node",
          "request": "launch",
          "cwd": "${workspaceFolder}/app/frontend",
          "runtimeExecutable": "pnpm",
          "runtimeArgs": ["run", "dev", "--", "--inspect"],
          "console": "integratedTerminal",
          "skipFiles": ["<node_internals>/**"]
        }
      ]
    }
    """
)


def remove_path(path: str) -> None:
    target = ROOT_DIR / path
    if not target.exists():
        return

    if target.is_dir():
        shutil.rmtree(target)
        print(f"Removed directory: {path}")
    else:
        target.unlink()
        print(f"Removed file: {path}")


def write_file(path: str, content: str) -> None:
    target = ROOT_DIR / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"Updated file: {path}")


def ensure_repo_root() -> None:
    expected = ROOT_DIR / "Makefile"
    if not expected.exists():
        print("Erro: execute este script a partir da raiz do repositório.", file=sys.stderr)
        sys.exit(1)


def configure_backend() -> None:
    remove_path("app/frontend")
    remove_path("infrastructure/docker/Dockerfile.frontend")
    remove_path("scripts/generate-types.sh")

    write_file("Makefile", BACKEND_MAKEFILE)
    write_file(".github/workflows/ci.yml", BACKEND_CI)
    write_file("infrastructure/docker-compose.yml", BACKEND_COMPOSE)
    print("\nConfiguração backend-only concluída. Revise README.md para ajustar documentação conforme necessário.")


def configure_frontend() -> None:
    remove_path("app/backend")
    remove_path("infrastructure/docker/Dockerfile.backend")

    write_file("Makefile", FRONTEND_MAKEFILE)
    write_file(".github/workflows/ci.yml", FRONTEND_CI)
    write_file("infrastructure/docker-compose.yml", FRONTEND_COMPOSE)
    write_file(".vscode/launch.json", FRONTEND_LAUNCH_JSON)
    print("\nConfiguração frontend-only concluída. Revise README.md para ajustar documentação conforme necessário.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ajusta o template para backend-only ou frontend-only.")
    parser.add_argument(
        "--mode",
        choices=("backend", "frontend"),
        required=True,
        help="Define qual parte do template deve permanecer ativa.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    ensure_repo_root()
    args = parse_args(argv)

    if args.mode == "backend":
        configure_backend()
    elif args.mode == "frontend":
        configure_frontend()
    else:
        raise ValueError(f"Modo inválido: {args.mode}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
