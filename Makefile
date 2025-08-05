.PHONY: help install install-dev test test-docker clean format lint type-check run test-connections setup

# Default target
help:
	@echo "Xibo Screen Updater - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup        - Run setup script"
	@echo "  make setup-dev    - Run setup script with dev dependencies"
	@echo "  make install      - Install dependencies only"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run pytest"
	@echo "  make test-docker  - Test setup in clean Docker environment"
	@echo "  make test-connections - Test NextCloud and Xibo connections"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format       - Format code with Black"
	@echo "  make lint         - Check code with flake8"
	@echo "  make type-check   - Type checking with mypy"
	@echo "  make check-all    - Run all code quality checks"
	@echo ""
	@echo "Running:"
	@echo "  make run          - Run the main application (uses ./config.yaml)"
	@echo "  make run-config   - Show config usage examples"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Clean up build files and cache"

# Setup
setup:
	./setup.sh

setup-dev:
	./setup.sh --dev

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest

test-docker:
	@echo "🧪 Testing setup in clean Docker environment..."
	docker run -it --rm -v $$(pwd):/app -w /app python:3.12 bash -c "chmod +x setup.sh && ./setup.sh && python -c 'import main, nextcloud_client, xibo_client; print(\"✅ All modules imported successfully\")'"

test-connections:
	@echo "🔌 Testing connections..."
	python test_nextcloud.py
	python test_xibo.py

# Code quality
format:
	black .

lint:
	flake8 .

type-check:
	mypy .

check-all: format lint type-check
	@echo "✅ All code quality checks completed"

# Running
run:
	python main.py

run-config:
	@echo "Usage examples:"
	@echo "  make run                                    # Uses ./config.yaml"
	@echo "  make run CONFIG=/path/to/config.yaml       # Uses specific config"
	@echo "  CONFIG_PATH=/path/to/config.yaml make run  # Uses environment variable"
	@if [ -n "$(CONFIG)" ]; then \
		python main.py -c $(CONFIG); \
	else \
		python main.py; \
	fi

# Maintenance
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/
	@echo "🧹 Cleaned up build files and cache"
