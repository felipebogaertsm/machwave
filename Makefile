test:
	@docker compose -f compose.test.yaml up --build --remove-orphans
publish:
	@twine upload dist/*
check:
	@poetry run ruff format
	@poetry run ruff check --fix
	@poetry run pyright machwave