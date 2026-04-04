.PHONY: install test publish check format generate-umls coverage docs docs-serve docs-deploy clean

install:
	@uv sync
test:
	@uv run pytest
publish:
	@uv build
	@twine upload dist/*
check:
	@uv run ruff format --check
	@uv run ruff check .
	@uv run pyright machwave
format:
	@uv run ruff format
	@uv run ruff check . --fix
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
clean:
	@rm -rf build dist site htmlcov .coverage
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true