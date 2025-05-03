test:
	@poetry run pytest
publish:
	@twine upload dist/*
check:
	@poetry run ruff format
	@poetry run ruff check --fix --select I
	@poetry run pyright machwave