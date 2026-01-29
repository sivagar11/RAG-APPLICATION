SHELL := /bin/bash

.PHONY: help install install-dev test test-verbose test-cov clean clean-storage clean-all lint format

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies (includes testing tools)
	pip install -r requirements-dev.txt

test:  ## Run all tests
	pytest

test-verbose:  ## Run tests with verbose output
	pytest -v

test-cov:  ## Run tests with coverage report
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-quick:  ## Run tests without coverage (faster)
	pytest --no-cov -v

test-config:  ## Run only configuration tests
	pytest tests/test_config.py -v

test-parse:  ## Run only parsing tests
	pytest tests/test_parse.py -v

test-app:  ## Run only app tests
	pytest tests/test_app.py -v

clean:  ## Clean Python cache files and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -f .coverage

clean-storage:  ## Clear vector store and index (WARNING: You'll need to re-run parse.py)
	@echo "⚠️  WARNING: This will delete your vector index!"
	@echo "You will need to run 'python parse.py' again to rebuild it."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf storage/*; \
		echo "✅ Storage cleared!"; \
	else \
		echo "❌ Cancelled."; \
	fi

clean-images:  ## Clear extracted images (WARNING: You'll need to re-run parse.py)
	@echo "⚠️  WARNING: This will delete extracted images!"
	@echo "You will need to run 'python parse.py' again to rebuild them."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data_images/*; \
		echo "✅ Images cleared!"; \
	else \
		echo "❌ Cancelled."; \
	fi

clean-all:  ## Clean everything (cache, storage, images) - DESTRUCTIVE!
	@echo "⚠️  WARNING: This will delete ALL generated data!"
	@echo "You will need to run 'python parse.py' again."
	@read -p "Are you ABSOLUTELY sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) clean; \
		rm -rf storage/*; \
		rm -rf data_images/*; \
		echo "✅ Everything cleaned!"; \
	else \
		echo "❌ Cancelled."; \
	fi

lint:  ## Run linting checks
	flake8 . --exclude=venv,build,dist
	mypy . --ignore-missing-imports --exclude=venv

format:  ## Format code with black and isort
	black . --exclude=venv
	isort . --skip venv

parse:  ## Run document parsing and indexing (REBUILDS index from scratch)
	python3 src/parse.py

add-batch:  ## Add PDFs to existing index without rebuilding
	python3 src/add_pdfs_batch.py

run:  ## Run the Streamlit app
	streamlit run src/app.py

api:  ## Run the FastAPI server
	cd src && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

api-prod:  ## Run the FastAPI server in production mode
	cd src && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

setup:  ## Initial setup: copy env.example to .env
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env file. Please edit it with your API keys!"; \
	else \
		echo "⚠️  .env already exists. Skipping..."; \
	fi

# === Qdrant Commands ===

qdrant-status:  ## Check Qdrant Cloud connection
	@python3 -c "from src.ingestion.vector_store import check_vector_db_connection; import sys; sys.exit(0 if check_vector_db_connection() else 1)" && \
		echo "✅ Qdrant Cloud connection OK" || \
		echo "❌ Qdrant Cloud connection failed"

qdrant-info:  ## Show Qdrant collection info
	@python3 -c "from src.ingestion import get_index; idx = get_index(); print(f'Documents: {len(idx.ref_doc_info)}')"

