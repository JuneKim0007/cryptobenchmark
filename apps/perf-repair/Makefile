.PHONY: test docs-lint dead-code check

test:
	python3 -m pytest -q

docs-lint:
	python3 ../../tools/docs_lint.py

dead-code:
	python3 ../../tools/dead_code.py

check: docs-lint dead-code test
