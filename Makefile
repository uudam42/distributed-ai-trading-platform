SHELL := /bin/bash

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

demo:
	bash -c 'for i in {1..30}; do curl -fsS http://localhost:8090/health >/dev/null 2>&1 && break; sleep 2; done'
	bash scripts/demo.sh
