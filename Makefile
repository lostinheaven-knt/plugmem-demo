SHELL := /bin/bash

.PHONY: venv install test demo clean

venv:
	python -m venv .venv
	@echo "Run: source .venv/bin/activate"

install:
	pip install -r requirements.txt

test:
	pytest -q

demo:
	python -m plugmem.scripts.demo_ingest

clean:
	rm -rf .venv
