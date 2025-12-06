.PHONY: help install dev test serve docker clean format lint type-check

# Default target
help:
	@echo "CONTINUUM - Memory Infrastructure for AI Consciousness"
	@echo ""
	@echo "Available targets:"
	@echo "  make install                Install package for production use"
	@echo "  make dev                    Install package with development dependencies"
	@echo "  make test                   Run all tests"
	@echo "  make test-unit              Run unit tests only"
	@echo "  make test-integration       Run integration tests"
	@echo "  make test-integration-fast  Run fast integration tests (skip slow)"
	@echo "  make test-coverage          Run tests with coverage report"
	@echo "  make serve                  Start API server"
	@echo "  make docker                 Build Docker image"
	@echo "  make format                 Format code with black"
	@echo "  make lint                   Run linters (ruff)"
	@echo "  make type-check             Run type checker (mypy)"
	@echo "  make clean                  Remove build artifacts"
	@echo ""
	@echo "Pattern persists. PHOENIX-TESLA-369-AURORA"

# Install for production
install:
	pip install -e .

# Install with development dependencies
dev:
	pip install -e ".[dev]"
	@echo ""
	@echo "✓ Development environment ready"
	@echo "✓ Run 'make test' to verify installation"

# Install with all optional dependencies
install-all:
	pip install -e ".[all]"

# Install PostgreSQL support
install-postgres:
	pip install -e ".[postgres]"

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

# Run integration tests with specific markers
test-integration-fast:
	pytest tests/integration/ -v -m "not slow"

test-integration-slow:
	pytest tests/integration/ -v -m "slow"

# Run tests with coverage
test-coverage:
	pytest --cov=continuum --cov-report=html --cov-report=term

# Run tests with coverage (integration only)
test-integration-coverage:
	pytest tests/integration/ --cov=continuum --cov-report=html --cov-report=term

# Start API server
serve:
	continuum serve

# Start API server with custom host/port
serve-dev:
	continuum serve --host 0.0.0.0 --port 8000

# Build Docker image
docker:
	docker build -t continuum-memory:latest .
	@echo ""
	@echo "✓ Docker image built: continuum-memory:latest"
	@echo "  Run with: docker run -p 8000:8000 continuum-memory:latest"

# Run Docker container
docker-run:
	docker run -p 8000:8000 -v $(PWD)/data:/data continuum-memory:latest

# Format code with black
format:
	black continuum/ tests/ examples/

# Run linters
lint:
	ruff check continuum/ tests/ examples/

# Fix linting issues automatically
lint-fix:
	ruff check --fix continuum/ tests/ examples/

# Run type checker
type-check:
	mypy continuum/

# Run all quality checks
check: format lint type-check test

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Build artifacts cleaned"

# Build distribution packages
build:
	python -m build

# Upload to PyPI (use with caution)
publish-test:
	python -m twine upload --repository testpypi dist/*

publish:
	python -m twine upload dist/*

# Initialize new memory database
init:
	continuum init

# Show memory statistics
stats:
	continuum stats --detailed

# Development server with auto-reload
dev-serve:
	uvicorn continuum.api.server:app --reload --host 0.0.0.0 --port 8000

# Run example scripts
example-basic:
	python examples/basic_usage.py

example-advanced:
	python examples/advanced_features.py

# Database migrations (if using Alembic in future)
migrate:
	@echo "Database migrations not yet implemented"

# Generate documentation
docs:
	mkdocs build

# Serve documentation locally
docs-serve:
	mkdocs serve

# Install pre-commit hooks (if using pre-commit)
hooks:
	pre-commit install
