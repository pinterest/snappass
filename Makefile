.PHONY: dev prod run test

dev:
	pip install .[dev]

prod:
	pip install .

run: prod
	FLASK_DEBUG=1 FLASK_APP=snappass.main NO_SSL=True flask run

test:
	tox
