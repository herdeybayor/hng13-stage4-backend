# Makefile for Distributed Notification System

.PHONY: help install start stop restart logs clean test build deploy

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Distributed Notification System - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ==============================================================================
# SETUP & INSTALLATION
# ==============================================================================

install: ## Install all dependencies for all services
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@for service in api-gateway user-service template-service email-service push-service; do \
		if [ -d $$service ]; then \
			echo "$(GREEN)Installing $$service dependencies...$(NC)"; \
			cd $$service && pip install -r requirements.txt && cd ..; \
		fi \
	done
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup: ## Initial project setup (copy env, create dirs)
	@echo "$(BLUE)Setting up project...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file already exists$(NC)"; \
	fi
	@mkdir -p logs
	@echo "$(GREEN)✓ Setup complete$(NC)"

init: setup install ## Complete initial setup (setup + install)
	@echo "$(GREEN)✓ Project initialized$(NC)"

# ==============================================================================
# DOCKER OPERATIONS
# ==============================================================================

build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Images built$(NC)"

start: ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@sleep 5
	@make status
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)Access points:$(NC)"
	@echo "  API Gateway: http://localhost:8000/docs"
	@echo "  User Service: http://localhost:8001/docs"
	@echo "  Template Service: http://localhost:8002/docs"
	@echo "  RabbitMQ Management: http://localhost:15672 (admin/admin123)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

down: ## Stop and remove all containers
	@echo "$(BLUE)Stopping and removing containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers removed$(NC)"

restart: stop start ## Restart all services

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API Gateway logs
	docker-compose logs -f api-gateway

logs-user: ## Show User Service logs
	docker-compose logs -f user-service

logs-template: ## Show Template Service logs
	docker-compose logs -f template-service

logs-email: ## Show Email Worker logs
	docker-compose logs -f email-worker

logs-push: ## Show Push Worker logs
	docker-compose logs -f push-worker

logs-rabbitmq: ## Show RabbitMQ logs
	docker-compose logs -f rabbitmq

# ==============================================================================
# DATABASE OPERATIONS
# ==============================================================================

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker-compose exec user-service alembic upgrade head
	docker-compose exec template-service alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(BLUE)Rolling back migration...$(NC)"
	docker-compose exec user-service alembic downgrade -1
	docker-compose exec template-service alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(NC)"

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)⚠ This will destroy all data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "$(BLUE)Resetting database...$(NC)"
	docker-compose down -v
	docker-compose up -d postgres redis rabbitmq
	@sleep 10
	docker-compose up -d user-service template-service
	@sleep 5
	@make db-migrate
	@echo "$(GREEN)✓ Database reset complete$(NC)"

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d notifications

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

# ==============================================================================
# SCALING
# ==============================================================================

scale-email: ## Scale email workers (usage: make scale-email n=5)
	@echo "$(BLUE)Scaling email workers to $(n) instances...$(NC)"
	docker-compose up -d --scale email-worker=$(n)
	@echo "$(GREEN)✓ Email workers scaled$(NC)"

scale-push: ## Scale push workers (usage: make scale-push n=3)
	@echo "$(BLUE)Scaling push workers to $(n) instances...$(NC)"
	docker-compose up -d --scale push-worker=$(n)
	@echo "$(GREEN)✓ Push workers scaled$(NC)"

# ==============================================================================
# TESTING
# ==============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@for service in api-gateway user-service template-service email-service push-service; do \
		if [ -d $$service/tests ]; then \
			echo "$(GREEN)Testing $$service...$(NC)"; \
			cd $$service && pytest tests/ -v && cd ..; \
		fi \
	done
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@for service in api-gateway user-service template-service email-service push-service; do \
		if [ -d $$service/tests ]; then \
			echo "$(GREEN)Testing $$service...$(NC)"; \
			cd $$service && pytest tests/ -v --cov=app --cov-report=html && cd ..; \
		fi \
	done
	@echo "$(GREEN)✓ Tests complete. Coverage reports in <service>/htmlcov/$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

load-test: ## Run load tests with Locust
	@echo "$(BLUE)Running load tests...$(NC)"
	locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 2m --headless

# ==============================================================================
# CODE QUALITY
# ==============================================================================

lint: ## Run linters (black, flake8, isort)
	@echo "$(BLUE)Running linters...$(NC)"
	black --check .
	flake8 . --max-line-length=120
	isort --check-only .
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

# ==============================================================================
# MONITORING
# ==============================================================================

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "API Gateway:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)✗ Down$(NC)"
	@echo "\nUser Service:"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "$(RED)✗ Down$(NC)"
	@echo "\nTemplate Service:"
	@curl -s http://localhost:8002/health | python -m json.tool || echo "$(RED)✗ Down$(NC)"

queue-stats: ## Show RabbitMQ queue statistics
	@echo "$(BLUE)Queue Statistics:$(NC)"
	@curl -s -u admin:admin123 http://localhost:15672/api/queues | python -m json.tool | grep -E '(name|messages|consumers)' || echo "$(RED)RabbitMQ not accessible$(NC)"

metrics: ## Show Prometheus metrics (if enabled)
	@echo "$(BLUE)Fetching metrics...$(NC)"
	@curl -s http://localhost:8000/metrics | head -20

# ==============================================================================
# CLEANUP
# ==============================================================================

clean: ## Clean up containers, volumes, and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-logs: ## Clean log files
	@echo "$(BLUE)Cleaning logs...$(NC)"
	rm -rf logs/*
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

prune: ## Prune Docker system (WARNING: removes unused images and volumes)
	@echo "$(RED)⚠ This will remove unused Docker resources!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Docker pruned$(NC)"

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev: ## Start services in development mode with hot reload
	@echo "$(BLUE)Starting in development mode...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

shell-api: ## Open shell in API Gateway container
	docker-compose exec api-gateway /bin/sh

shell-user: ## Open shell in User Service container
	docker-compose exec user-service /bin/sh

shell-template: ## Open shell in Template Service container
	docker-compose exec template-service /bin/sh

# ==============================================================================
# DOCUMENTATION
# ==============================================================================

docs: ## Open API documentation in browser
	@echo "$(BLUE)Opening API documentation...$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

api-spec: ## Generate OpenAPI specification
	@echo "$(BLUE)Generating API spec...$(NC)"
	@curl http://localhost:8000/openapi.json > api-spec.json
	@echo "$(GREEN)✓ API spec saved to api-spec.json$(NC)"

# ==============================================================================
# DEPLOYMENT
# ==============================================================================

deploy-prod: ## Deploy to production (requires SSH access)
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(RED)⚠ This will deploy to production!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "$(BLUE)Building production images...$(NC)"
	docker-compose -f docker-compose.prod.yml build
	@echo "$(BLUE)Pushing images...$(NC)"
	docker-compose -f docker-compose.prod.yml push
	@echo "$(GREEN)✓ Deployment initiated$(NC)"

backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U postgres notifications > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup created in backups/ directory$(NC)"

restore: ## Restore database from backup (usage: make restore file=backups/backup_YYYYMMDD_HHMMSS.sql)
	@echo "$(BLUE)Restoring database from $(file)...$(NC)"
	docker-compose exec -T postgres psql -U postgres notifications < $(file)
	@echo "$(GREEN)✓ Database restored$(NC)"

# ==============================================================================
# QUICK COMMANDS
# ==============================================================================

all: clean build start db-migrate ## Complete rebuild (clean, build, start, migrate)
	@echo "$(GREEN)✓ Complete rebuild finished$(NC)"

quick: ## Quick start for development
	@make setup
	@make start
	@echo "$(GREEN)✓ Quick start complete$(NC)"

