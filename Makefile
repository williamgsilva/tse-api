# Interface ÚNICA de comandos. A CI chama os mesmos alvos que você roda localmente.
# Backend: Python (venv em .venv). Frontend: Node (frontend/).

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

IMAGE ?= tse-api
TAG   ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

VENV   ?= .venv
PY     := $(VENV)/bin/python
BIN    := $(VENV)/bin
NPM    := npm --prefix frontend
# Cobertura mínima em domain e application (docs/standards/testes.md).
COVERAGE_MIN ?= 80

# Carrega o .env (se existir) para run/ingest; variáveis já exportadas têm precedência.
LOAD_ENV := set -a; [ -f .env ] && . ./.env; set +a

.PHONY: help setup lint format test security sbom build run dev ingest check clean

help: ## Lista os comandos disponíveis
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(PY):
	python3 -m venv $(VENV)

setup: $(PY) ## Prepara o ambiente local (dependências, git hooks e .env)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -e '.[dev]'
	$(NPM) ci
	@[ -f .env ] || cp .env.example .env
	@if command -v pre-commit >/dev/null; then pre-commit install; \
		else echo "AVISO: instale o pre-commit (pipx install pre-commit) e rode 'pre-commit install'"; fi

lint: ## Lint, tipos, arquitetura e formatação (backend e frontend)
	@if command -v pre-commit >/dev/null; then SKIP=no-commit-to-branch pre-commit run --all-files; \
		else echo "AVISO: pre-commit não instalado — hooks genéricos só na CI"; fi
	$(BIN)/ruff check src tests
	$(BIN)/ruff format --check src tests
	$(BIN)/mypy
	$(BIN)/lint-imports
	$(NPM) run lint

format: ## Formata o código
	$(BIN)/ruff format src tests
	$(BIN)/ruff check --fix src tests
	$(NPM) run format

test: ## Testes com cobertura (backend ≥ $(COVERAGE_MIN)% em domain/application; frontend pelo vitest)
	$(BIN)/pytest --cov --cov-report=term --cov-report=xml:reports/coverage.xml
	$(BIN)/coverage report --include='*/domain/*,*/application/*' --fail-under=$(COVERAGE_MIN)
	$(NPM) test

security: ## Segredos, vulnerabilidades, misconfig e licenças (falha se encontrar algo)
	@if command -v gitleaks >/dev/null; then gitleaks git --redact .; \
		else echo "AVISO: gitleaks não instalado — varredura de segredos só na CI"; fi
	@if command -v trivy >/dev/null; then \
		trivy fs --scanners vuln,secret,misconfig,license --severity HIGH,CRITICAL --exit-code 1 .; \
		else echo "AVISO: trivy não instalado — varredura de vulnerabilidades só na CI"; fi

sbom: ## Gera o SBOM (CycloneDX) em reports/sbom.cdx.json
	@command -v trivy >/dev/null || { echo "Instale o trivy: https://trivy.dev"; exit 1; }
	@mkdir -p reports
	trivy fs --format cyclonedx --output reports/sbom.cdx.json .

build: ## Gera a imagem Docker (API + frontend)
	docker build -t $(IMAGE):$(TAG) .

run: ## Sobe a API em APP_PORT (padrão 8000), servindo o frontend de frontend/dist se existir
	$(LOAD_ENV); $(BIN)/uvicorn tse_api.bootstrap.app:create_app --factory --reload \
		--host "$${APP_HOST:-127.0.0.1}" --port "$${APP_PORT:-8007}"

dev: ## Frontend em modo desenvolvimento (Vite em :5173, repassando /v1 para a API)
	$(LOAD_ENV); VITE_API_PROXY="http://127.0.0.1:$${APP_PORT:-8000}" $(NPM) run dev

ingest: ## Importa CSVs de boletins de urna (ex.: make ingest ARGS="--turno 1 2 --uf AC SP")
	$(LOAD_ENV); $(BIN)/tse-ingest $(ARGS)

check: lint test security ## Tudo que a CI valida

clean: ## Remove artefatos gerados (não apaga data/)
	rm -rf dist build out coverage reports tmp frontend/dist frontend/coverage .pytest_cache .mypy_cache .ruff_cache
