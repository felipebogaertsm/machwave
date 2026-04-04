.PHONY: install test publish check generate-umls coverage docs docs-serve docs-deploy

install:
	@uv sync
test:
	@uv run pytest
publish:
	@uv build
	@twine upload dist/*
check:
	@uv run ruff format
	@uv run ruff check . --fix
	@uv run pyright machwave
generate-umls:
	@zsh ./scripts/generate-umls.sh
coverage:
	@uv run pytest --cov=machwave --cov-branch --cov-report=term-missing --cov-report=html tests/
docs:
	@uv run mkdocs build
docs-serve:
	@uv run mkdocs serve --watch machwave
docs-deploy:
	@uv run mkdocs build --strict