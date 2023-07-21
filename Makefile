.DEFAULT_GOAL:=help
.ONESHELL:
ENV_PREFIX=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
VENV_EXISTS=$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
VERSION := $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)
SRC_DIR=.
BUILD_DIR=dist

.EXPORT_ALL_VARIABLES:

ifndef VERBOSE
.SILENT:
endif


help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


.PHONY: upgrade
upgrade:       ## Upgrade all dependencies to the latest stable versions
	@if [ "$(USING_POETRY)" ]; then poetry update; fi
	@echo "Python Dependencies Updated"
	$(ENV_PREFIX)pre-commit autoupdate
	@echo "Updated Pre-commit"

.PHONY: install
install:          ## Install the project in dev mode.
	@if ! poetry --version > /dev/null; then echo 'poetry is required, installing from from https://install.python-poetry.org'; curl -sSL https://install.python-poetry.org | python3 -; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "Removing existing virtual environment"; fi
	if [ "$(VENV_EXISTS)" ]; then rm -Rf .venv; fi
	if [ "$(USING_POETRY)" ]; then poetry config virtualenvs.in-project true --local  && poetry config virtualenvs.options.always-copy true --local && python3 -m venv --copies .venv && source .venv/bin/activate && .venv/bin/pip install -U wheel setuptools cython pip && poetry install --with dev; fi
	@echo "=> Install complete.  ** If you want to re-install re-run 'make install'"


.PHONY: migrations
migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will create a new database migration for any defined models changes."
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=. $(ENV_PREFIX)alembic -c spannermc/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"

.PHONY: migrate
migrate:          ## Generate database migrations
	@echo "ATTENTION: Will apply all database migrations."
	@env PYTHONPATH=. $(ENV_PREFIX)spannermc database upgrade

.PHONY: squash-migrations
squash-migrations:       ## Generate database migrations
	@echo "ATTENTION: This operation will wipe all migrations and recreate from an empty state."
	@env PYTHONPATH=. $(ENV_PREFIX)spannermc database purge --no-prompt
	rm -Rf spannermc/lib/db/migrations/versions/*.py
	@while [ -z "$$MIGRATION_MESSAGE" ]; do read -r -p "Initial migration message: " MIGRATION_MESSAGE; done ;
	@env PYTHONPATH=. $(ENV_PREFIX)alembic -c spannermc/lib/db/alembic.ini revision --autogenerate -m "$${MIGRATION_MESSAGE}"


.PHONY: build
build:
	@echo "=> Building package..."
	if [ "$(USING_POETRY)" ]; then poetry build; fi
	@echo "=> Building and pushing container to Docker Hub..."
	source ./.gcloud.env && docker build -f deploy/docker/run/Dockerfile .  --tag "$$_CONTAINER_IMAGE" && docker push "$$_CONTAINER_IMAGE"

.PHONY: test
test:
	@echo "=> Launching Python test cases..."
	$(ENV_PREFIX)pytest tests/

.PHONY: lint
lint:
	@echo "=> Executing pre-commit..."
	$(ENV_PREFIX)pre-commit run --all-files

gen-docs:       ## generate HTML documentation
	$(ENV_PREFIX)mkdocs build

.PHONY: docs
docs:       ## generate HTML documentation and serve it to the browser
	$(ENV_PREFIX)mkdocs build
	$(ENV_PREFIX)mkdocs serve


.PHONY: clean
clean:       ## remove all build, testing, and static documentation files
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.ipynb_checkpoints' -exec rm -fr {} +
	rm -fr .tox/
	rm -fr .coverage
	rm -fr coverage.xml
	rm -fr coverage.json
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .mypy_cache
	rm -fr site

.PHONY: deploy
deploy:												## Deploy to cloudrun

	@echo "=> Deploying to Google CloudRun..."
	source ./.gcloud.env && gcloud config set project $$_PROJECT_ID && gcloud builds submit --config=deploy/gcp/cloudbuild.deploy.yml  --substitutions=_PROJECT_ID="$$_PROJECT_ID",_REGION_NAME="$$_REGION_NAME",_SERVICE_NAME="$$_SERVICE_NAME",_SERVICE_ACCOUNT="$$_SERVICE_ACCOUNT",_VPC_NAME="$$_VPC_NAME",_ENV_SECRETS="$$_ENV_SECRETS",_MEMORY_SIZE="$$_MEMORY_SIZE",_MAX_INSTANCES="$$_MAX_INSTANCES",BRANCH_NAME="main",SHORT_SHA="$$(git rev-parse --short HEAD)"

.PHONY: proxy
proxy:												## start proxt to cloudrun

	@echo "=> Starting Google CloudRun Proxt..."
	source ./.gcloud.env && gcloud config set project $$_PROJECT_ID && gcloud beta run services proxy $$_SERVICE_NAME --project $$_PROJECT_ID --port 8083 --region $$_REGION_NAME
