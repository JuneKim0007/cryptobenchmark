#!/usr/bin/env python3
"""One command for benchmark then guided repair, from one settings index: apps/cli/facade.py --settings <settings.yaml> [--check]"""
import argparse
import sys

import facade  # noqa: F401  first: it names a missing library and puts the benchmark runner on the path

# isort: split
import dependencies  # noqa: F401  next: it reports a missing PyYAML, which everything below needs
import timeouts
from facade import tree
from facade.check import check
from facade.phases import run_phases
from facade.tree import CATALOG
from failure import one_line


def _report(checked):
    """One coded line for the check; the problems past the first come before it, so the last line is the outcome."""
    if not checked.problems:
        files = sum(n.kind != CATALOG for n in checked.nodes)
        catalogs = len(checked.nodes) - files
        print("\n".join(tree.lines(checked.nodes)))
        print(f"facade check: check_ok: {files} nodes, {catalogs} catalogs")
        return 0
    for problem in checked.problems[1:]:
        print(f"check: {one_line(problem)}")
    more = f" (and {len(checked.problems) - 1} more above)" if len(checked.problems) > 1 else ""
    print(f"facade check: {one_line(checked.problems[0])}{more}")
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", required=True, metavar="FILE", help="the root settings index (settings.example.yaml)")
    parser.add_argument("--check", action="store_true",
                        help="resolve and verify the tree, then stop: no app build, no device, no model; the parsers of "
                             "global.yaml run on the JVM through the host tool, which Gradle compiles on first use")
    options = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    checked = check(options.settings)
    code = _report(checked)
    if options.check:
        return code
    if code != 0:
        print("facade crypto: crypto_not_run: the check failed")
        print("facade guided: guided_not_run: the check failed")
        return code
    return run_phases(checked.index, tree.document(checked.nodes))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, timeouts.StepTimeout) as error:
        print(f"facade: {one_line(error)}")
        sys.exit(1)
