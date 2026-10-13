.PHONY: test docs-lint check

test:
	python3 -m pytest -q

docs-lint:
	python3 scripts/docs_lint.py

check: docs-lint test
