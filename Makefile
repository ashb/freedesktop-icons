.PHONY: help init build test htmlcov lint pretty precommit_install bump_major bump_minor bump_patch docs

BIN = .venv/bin/
CODE = "freedesktop_icons"

help: # Make help to show possible targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

test:  ## Test the project
	poetry run pytest --verbosity=2 --log-level=DEBUG --cov="$(CODE)" $(args)

htmlcov:  ## Tests the project with html coverage report
	$(MAKE) test args="--cov-report=html:htmlcov $(args)"

build:  ## Build the sdist/wheel packages
	poetry build

docs:  ## Build HTML docs
	poetry run $(MAKE) -C docs/ html

lint:  ## Check code for style
	pre-commit run --all-files
	poetry run pytest --dead-fixtures --dup-fixtures

pretty: ## Prettify the code
	poetry run isort $(CODE) tests
	poetry run black $(CODE) tests

precommit_install: ## Install simple pre-commit checks
	pre-commit install

bump_major: ## Release a new major version
	poetry run bumpversion major

bump_minor: ## Release a new minor version
	poetry run bumpversion minor

bump_patch: ## Release a new patch version
	poetry run bumpversion patch
