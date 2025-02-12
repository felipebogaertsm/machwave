test:
	@docker compose -f compose.test.yaml up
publish:
	@twine upload dist/*