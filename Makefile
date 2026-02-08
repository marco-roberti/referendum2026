.PHONY: all test lint format clean

PYTHON ?= python

all: format lint test

test:
	$(PYTHON) -m pytest tests/ --cov=sondaggi --cov-report=term-missing --cov-report=html -v

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

clean:
	rm -rf .pytest_cache .coverage htmlcov
	rm -f *.png *.csv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
