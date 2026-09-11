.PHONY: install install-all install-dev install-dev-core install-docs install-hooks test test-core benchmark publish build verify-version check format-check lint typecheck format generate-umls coverage docs docs-serve docs-deploy clean

install:
	@uv sync

install-all:
	@uv sync --all-extras

install-dev:
	@uv sync --all-extras --group dev

# The core environment: no extras, so the tooling is there but the optional
# dependencies are not. Drives the test-core target.
install-dev-core:
	@uv sync --group dev

install-docs:
	@uv sync --all-extras --group docs --group dev

install-hooks:
	@uv run pre-commit install

build:
	@uv build

verify-version:
	@PKG_VERSION=$$(uv run python -c "ns = {}; exec(open('machwave/_version.py').read(), ns); print(ns['__version__'])"); \
	TAG_VERSION=$${GITHUB_REF_NAME#v}; \
	if [ "$$PKG_VERSION" != "$$TAG_VERSION" ]; then \
		echo "::error::Tag version ($$TAG_VERSION) does not match package version ($$PKG_VERSION)"; \
		exit 1; \
	fi; \
	echo "Version verified: $$PKG_VERSION"
test:
	@uv run pytest -n auto
# Selects by path rather than by marker: testpaths collects the whole suite
# before deselecting, and most of it cannot be imported without the extras.
test-core:
	@uv run pytest -n auto \
		tests/test_optional_dependencies.py \
		tests/test_common \
		tests/test_core \
		tests/test_services/test_eng.py \
		--ignore=tests/test_core/test_two_phase_flow.py
benchmark:
	@uv run pytest tests/benchmarks --benchmark-only --benchmark-columns=min,median,mean,stddev,rounds
publish:
	@$(MAKE) build
	@twine upload dist/*
check: format-check lint typecheck
format-check:
	@uv run ruff format --check
lint:
	@uv run ruff check .
typecheck:
	@uv run pyright machwave
format:
	@uv run ruff format
	@uv run ruff check . --fix
generate-umls:
	@zsh ./scripts/generate-umls.sh
coverage:
	@uv run pytest --cov=machwave --cov-branch --cov-report=term-missing --cov-report=html --cov-report=xml tests/
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
