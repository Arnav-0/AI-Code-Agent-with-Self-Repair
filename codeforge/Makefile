.PHONY: install dev test-unit test-integration test-e2e test-all lint format type-check \
        migrate migration docker-up docker-down dev-services dev-services-down \
        benchmark-humaneval benchmark-mbpp benchmark-custom benchmark-all \
        build-sandbox clean

install:
	pip install -e '.[dev]'

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test-unit:
	cd backend && pytest tests/unit -v --tb=short

test-integration:
	cd backend && pytest tests/integration -v --tb=short

test-e2e:
	cd backend && pytest tests/e2e -v --tb=short

test-all:
	cd backend && pytest --cov=app --cov-report=term-missing

lint:
	cd backend && ruff check app/ tests/

format:
	cd backend && ruff format app/ tests/

type-check:
	cd backend && mypy app/

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

dev-services:
	docker-compose -f docker-compose.dev.yml up -d

dev-services-down:
	docker-compose -f docker-compose.dev.yml down

benchmark-humaneval:
	python -m benchmarks.runner --type humaneval

benchmark-mbpp:
	python -m benchmarks.runner --type mbpp

benchmark-custom:
	python -m benchmarks.runner --type custom

benchmark-all:
	python -m benchmarks.runner --type all

build-sandbox:
	docker/sandbox/build.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; find . -type f -name '*.pyc' -delete
