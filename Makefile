.PHONY: dev test lint build clean setup

setup:
	cp .env.example .env
	pip install pre-commit
	pre-commit install
	cd frontend && npm install

dev:
	docker compose up --build

dev-backend:
	docker compose up --build postgres localstack recruitment training performance ai-assistant analytics

test:
	docker compose -f docker-compose.test.yml up -d
	for svc in shared recruitment training performance ai-assistant analytics; do \
		pytest services/$$svc/tests -v; \
	done
	docker compose -f docker-compose.test.yml down

lint:
	ruff check services/
	cd frontend && node --check src/server.js

security:
	bandit -r services/ -ll -q
	for svc in shared recruitment training performance ai-assistant analytics; do \
		safety check -r services/$$svc/requirements.txt; \
	done

docs:
	cd docs && bash generate.sh

build:
	docker compose build

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
