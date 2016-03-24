pip=venv/bin/pip
pytest=venv/bin/py.test
python=venv/bin/python

init:
	@if [ ! -d venv ]; then \
		virtualenv venv ; \
		$(pip) install -q -r requirements.txt ; \
		$(pip) install -e . ; \
	fi

test: init
	$(pytest) -q test_icecake.py

freeze:
	$(pip) freeze > requirements.txt

publish:
	$(python) setup.py register
	$(python) setup.py sdist upload
