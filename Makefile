.PHONY: docs tests

prepare-docs:       ## Build docs and prepare commit on gh-pages branch.
	@./scripts/docs/docs.sh

docs:               ## Open docs.
	@pdoc -t scripts/docs jsonapy

install-pre-commit: ## Install pre-commit hook script.
	@./scripts/pre-commit/install-pre-commit.sh

tests:              ## Run tests with coverage.
	@pytest --cov jsonapy tests

coverage: tests     ## Generate HTML coverage report and open it.
	@coverage html && xdg-open htmlcov/index.html

clean:              ## Clean the coverage files.
	@rm -rf htmlcov .coverage coverage.xml

help:               ## Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)
