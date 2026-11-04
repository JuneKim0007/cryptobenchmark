"""Generates and compiles a harness's scopes alone, leaving the sources in place."""
import sys

from repo import BENCHMARK
from scope.generate import generate


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: scope_generate.py <harness.yaml> <output directory>")
    path, ids = generate(sys.argv[1], BENCHMARK, sys.argv[2])
    print(f"wrote:     {path} ({len(ids)} compiled)")
