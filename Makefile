.PHONY: install
install:
	pipenv install --dev

.PHONY: test
test:
	pipenv run coverage run -m pytest
	pipenv run coverage html
	pipenv run coverage report

.PHONY: lint
lint:
	pipenv run black simple_hd44780/
	pipenv run black tests/
	pipenv run black tester.py

.PHONY: run
run:
	pipenv run python tester.py