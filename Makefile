test:
	@docker compose -f docker-compose-test.yaml up
publish:
	@twine upload dist/*