test:
	@docker compose -f docker-compose-test.yaml up --build --remove-orphans
publish:
	@twine upload dist/*