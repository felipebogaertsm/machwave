test:
	@docker compose -f compose.test.yaml up --build --remove-orphans
publish:
	@twine upload dist/*