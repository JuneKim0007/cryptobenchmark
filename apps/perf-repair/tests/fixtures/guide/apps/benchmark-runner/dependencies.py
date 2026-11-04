"""Stands in for apps/benchmark-runner/dependencies.py; FAKE_MISSING_DEPENDENCY names the module it reports missing."""
import os
import sys

missing = os.environ.get("FAKE_MISSING_DEPENDENCY")
if missing:
    print(f"error: missing_dependency: {missing}; pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)
