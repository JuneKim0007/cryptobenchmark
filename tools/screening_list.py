"""Writes apps/perf-repair/docs/screening-list.md from the screening catalog: status counts per engine type, then every deprecated row."""
import collections
import pathlib

import yaml

from cryptobench import paths

ROOT = paths.code_root()

CATALOG = paths.repo().perf_repair_source / "perfrepair/catalog/screening.yaml"
DOC = ROOT / "apps/perf-repair/docs/screening-list.md"
UNSOURCED = "unsourced"


def cell(text):
    return str(text).replace("|", "\\|")


def link(source, sources):
    return UNSOURCED if source == UNSOURCED else f"[{source}]({sources[source]})"


def count_rows(crypto):
    """Status counts per engine type; every row, whatever its status."""
    for engine, rows in crypto.items():
        counts = collections.Counter(row["status"] for row in rows.values())
        yield f"| {engine} | {counts['deprecated']} | {counts['accepted']} |"


def deprecated(section, sources):
    return [f"| `{cell(name)}` | {cell(row['reason'])} | {link(row['source'], sources)} |"
            for name, row in section.items() if row["status"] == "deprecated"]


def table(heading, rows):
    return [f"## {heading}", "", "| Name | Reason | Source |", "|---|---|---|", *rows, ""] if rows else []


def render(doc):
    sources = doc["sources"]
    lines = ["# Screening list", "",
             "- source: `src/perfrepair/catalog/screening.yaml`.", "- a name in no row is `unknown`.", "- statuses: [screening.md](screening.md).", "",
             "## Counts", "", "| Engine type | deprecated | accepted |", "|---|---|---|", *count_rows(doc["crypto"]), ""]
    for engine, parts in doc["components"].items():
        for part, rules in parts.items():
            lines += table(f"{engine} {part} rules", deprecated(rules, sources))
    for engine, rows in doc["crypto"].items():
        lines += table(f"{engine} deprecated", deprecated(rows, sources))
    return "\n".join(lines)


if __name__ == "__main__":
    DOC.write_text(render(yaml.safe_load(CATALOG.read_text())))
    print(f"wrote:     {DOC.relative_to(ROOT)}")
