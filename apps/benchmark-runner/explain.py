"""Print the settings a run resolved to, and where each came from: effective.yaml's generatedFrom.settings, which :config writes."""
import argparse
import sys


from cryptobench.shared.settings import effective_view
from cryptobench.shared import paths
from cryptobench.shared.results import select
from failure import reported
from cryptobench.shared.document.document import read_yaml

SECTIONS = ("run", "policy", "analysis")


def flatten(value, prefix=""):
    if isinstance(value, dict) and value:
        for key, inner in value.items():
            yield from flatten(inner, f"{prefix}{key}.")
    else:
        yield prefix.rstrip("."), value


def explain(effective_file):
    effective = read_yaml(effective_file)
    sources = effective_view.required(effective, "generatedFrom.settings")
    rows = []
    for section in SECTIONS:
        for dotted, value in flatten(effective.get(section) or {}, f"{section}."):
            rows.append((dotted, value, sources.get(dotted, "default")))
    entries = effective_view.entry_count(effective)
    testset = (effective.get("generatedFrom") or {}).get("testSet", "?")
    return rows, entries, testset, effective.get("runId")


def main():
    parser = argparse.ArgumentParser(description="show each resolved setting and where it came from")
    parser.add_argument("--results", default=str(paths.repo().default_results), help="results root (default: results/)")
    parser.add_argument("--device-id", help="the folder under the results root; needed when it holds several")
    options = parser.parse_args()
    effective = paths.RunTree(select.device_folder(options.results, options.device_id)).configuration.effective
    if not effective.is_file():
        sys.exit(f"missing_file: {effective}")
    rows, entries, testset, run_id = explain(effective)
    width = max(len(dotted) for dotted, _, _ in rows)
    print(f"run id:  {run_id or '-'}")
    for dotted, value, source in rows:
        print(f"{dotted.ljust(width)}  {str(value):<40} {source}")
    print(f"providers: {entries} entries, selected by {testset}")


if __name__ == "__main__":
    with reported():
        main()
