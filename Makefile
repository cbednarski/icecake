pip=venv/bin/pip
pytest=venv/bin/py.test
python=venv/bin/python

build: init
	pandoc -f markdown -t rst README.md > README.rst
	$(python) generate.py
	$(MAKE) test

init:
	@if [ ! -d venv ]; then \
		virtualenv venv ; \
		$(pip) install -q -r requirements.txt ; \
		$(pip) install -e . ; \
	fi

test: init
	$(pytest)

freeze:
	$(pip) freeze > requirements.txt

publish:
	$(python) setup.py register
	$(python) setup.py sdist upload

inspect:
	$(python) setup.py sdist && tar -tzf dist/icecake-0.2.0.tar.gz