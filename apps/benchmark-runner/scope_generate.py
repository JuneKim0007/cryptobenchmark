"""Generates and compiles a harness's scopes alone, leaving the sources in place."""
import sys

from cryptobench.shared import paths
from cryptobench.shared.log.stdout import WROTE, say
from cryptobench.stages.verification.scope.generate import generate


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: scope_generate.py <harness.yaml> <output directory>")
    path, ids = generate(sys.argv[1], paths.repo().gradle_root, sys.argv[2])
    say(WROTE, f"{path} ({len(ids)} compiled)")
