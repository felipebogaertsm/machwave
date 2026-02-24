.PHONY: install test test-docker publish check generate-umls coverage docs docs-serve docs-deploy

install:
	@poetry install
test:
	@poetry run pytest
test-docker:
	@docker compose -f compose.test.yaml up --build --exit-code-from test-machwave
publish:
	@twine upload dist/*
check:
	@poetry run ruff format
	@poetry run ruff check . --fix
	@poetry run pyright machwave
generate-umls:
	@zsh ./scripts/generate-umls.sh
coverage:
	@poetry run pytest --cov=machwave --cov-branch --cov-report=term-missing --cov-report=html tests/
docs:
	@poetry run mkdocs build
docs-serve:
	@poetry run mkdocs serve --watch machwave
docs-deploy:
	@poetry run mkdocs build --strict