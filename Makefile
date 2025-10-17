.PHONY: help up down build logs restart clean test

help:
	@echo "SemiPrime Factor - Makefile Commands"
	@echo ""
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make build      - Rebuild all containers"
	@echo "  make logs       - Follow logs from all services"
	@echo "  make restart    - Restart all services"
	@echo "  make clean      - Remove containers, volumes, and images"
	@echo "  make test       - Run tests"
	@echo ""

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

restart:
	docker compose restart

clean:
	docker compose down -v --rmi all

test:
	@echo "Running backend tests..."
	cd api && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test
