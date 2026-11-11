"""A provider override `<path>: <value>`: where a path lands in an entry, and how one build's differences apply to a copy of it."""
from __future__ import annotations

ROW_SECTIONS = ("required", "optional")


def override_parent(base: dict, path: str) -> tuple[dict, str] | None:
    """A provider override `a.b.c`: the mapping that holds c; a list step picks the item named, or the fact, b."""
    *steps, last = path.split(".")
    node = base
    for step in steps:
        if isinstance(node, dict):
            node = node.get(step)
        elif isinstance(node, list):
            node = next((x for x in node if isinstance(x, dict) and step in (x.get("name"), x.get("fact"))), None)
        else:
            return None
    return (node, last) if isinstance(node, dict) and last and steps and steps[0] != "providers" else None


def row_override(path: str) -> tuple[str, str] | None:
    """required.<name> or optional.<name>: a build's whole row; (section, name), else None."""
    steps = path.split(".")
    return (steps[0], steps[1]) if len(steps) == 2 and steps[0] in ROW_SECTIONS else None


def apply_override(view: dict, path: str, value) -> None:
    """One build's difference on a copy of the entry: a field by its path; a whole row added or replaced, or null when this build runs without it."""
    row = row_override(path)
    if row is None:
        parent, key = override_parent(view, path)
        parent[key] = value
        return
    section, name = row
    kept = [r for r in view[section] if r.get("name") != name]
    view[section] = kept if value is None else [*kept, value]
