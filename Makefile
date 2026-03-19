.PHONY: help install test lint format clean run docker-build docker-up docker-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	uv pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest -v --cov=src --cov-report=term-missing

lint: ## Run linters
	ruff check src/ tests/
	mypy src/

format: ## Auto-format code
	black src/ tests/
	isort src/ tests/

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +

run: ## Run the application
	uvicorn keepcontext_ai.main:get_app --factory --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all Docker Compose services
	docker-compose down
