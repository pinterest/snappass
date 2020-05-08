dev: dev-requirements.txt
	pip install -r dev-requirements.txt

run: requirements.txt
	FLASK_DEBUG=1 FLASK_APP=snappass.main NO_SSL=True venv/bin/flask run

test:
	PYTHONPATH=snappass venv/bin/nosetests -s tests
