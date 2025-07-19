test:
	@poetry run pytest
test-docker:
	@docker compose -f compose.test.yaml up --build --exit-code-from test-machwave
publish:
	@twine upload dist/*
check:
	@poetry run ruff format
	@poetry run ruff check --fix --select I
	@poetry run pyright machwave
generate-umls:
	@zsh ./scripts/generate-umls.sh