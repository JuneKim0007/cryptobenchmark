"""Print the settings a run resolved to, and where each came from.

The source is read from what the files say, never from a second copy of the defaults:
a key written in the global file is that file's, any other key in the effective file is a default.
"""
import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECTIONS = ("run", "policy", "analysis")


def flatten(value, prefix=""):
    if isinstance(value, dict) and value:
        for key, inner in value.items():
            yield from flatten(inner, f"{prefix}{key}.")
    else:
        yield prefix.rstrip("."), value


def written(document, dotted):
    """True when the dotted key is spelled out in the authored document."""
    node = document
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def explain(global_file, effective_file):
    authored = yaml.safe_load(pathlib.Path(global_file).read_text()) or {}
    effective = yaml.safe_load(pathlib.Path(effective_file).read_text()) or {}
    rows = []
    for section in SECTIONS:
        for dotted, value in flatten(effective.get(section) or {}, f"{section}."):
            rows.append((dotted, value, pathlib.Path(global_file).name if written(authored, dotted) else "default"))
    entries = sum(len(names) for types in (effective.get("providers") or {}).values() for names in types.values())
    testset = (effective.get("generatedFrom") or {}).get("testSet", "?")
    return rows, entries, testset, effective.get("runId")


def main():
    parser = argparse.ArgumentParser(description="show each resolved setting and where it came from")
    parser.add_argument("--config", default=str(ROOT / "config/global.yaml"), help="the global file the run used")
    parser.add_argument("--results", default=str(ROOT / "results"), help="output root (default: results/)")
    options = parser.parse_args()
    effective = pathlib.Path(options.results) / "configuration" / "effective.yaml"
    for path in (pathlib.Path(options.config), effective):
        if not path.is_file():
            sys.exit(f"missing_file: {path}")
    rows, entries, testset, run_id = explain(options.config, effective)
    width = max(len(dotted) for dotted, _, _ in rows)
    print(f"run id:  {run_id or '-'}")
    for dotted, value, source in rows:
        print(f"{dotted.ljust(width)}  {str(value):<40} {source}")
    print(f"providers: {entries} entries, selected by {testset}")


if __name__ == "__main__":
    main()
