.PHONY: docs

docs:
	@./scripts/docs/docs.sh

install-pre-commit:
	@echo Copying pre-commit file in git hooks directory...
	@cp ./scripts/pre-commit ./.git/hooks/pre-commit
	@echo Granting execution permission...
	@chmod +x ./.git/hooks/pre-commit
	@echo Done.
