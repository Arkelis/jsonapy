.PHONY: docs tests

docs:
	@./scripts/docs/docs.sh

install-pre-commit:
	@./scripts/pre-commit/install-pre-commit.sh

tests:
	@pytest --cov jsonapy tests

coverage: tests
	@coverage html && xdg-open htmlcov/index.html

clean:
	@rm -rf htmlcov .coverage coverage.xml
