.PHONY: test docs-lint check coverage-guide

test:
	python3 -m pytest -q

docs-lint:
	python3 ../scripts/docs_lint.py

check: docs-lint test

# real-run coverage, needs `coverage`: make coverage-guide ARGS='--perfrepair-config my.yaml'; runs add up in OUT
OUT ?= runs/coverage
coverage-guide:
	mkdir -p $(OUT)
	-PYTHONPATH=src python3 -m coverage run -a --data-file=$(OUT)/.coverage --source=src/perfrepair -m perfrepair guide $(ARGS)
	python3 tools/unrun.py $(OUT)/.coverage src/perfrepair > $(OUT)/unrun.txt
	@echo "$(OUT)/unrun.txt: $$(wc -l < $(OUT)/unrun.txt) functions no run executed"
