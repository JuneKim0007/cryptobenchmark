from __future__ import annotations

from ..dto.grouping import Item
import re

from ..dto.screen import CODE_GROUPED, STATUSES, UNKNOWN, Verdict, read_screen, read_screen_catalog

SHA256 = re.compile(r"[0-9a-f]{64}")


def _verdict_problems(n: int, v: Verdict) -> list[str]:
    checks = ((v.status not in STATUSES, f"status {v.status!r} is not one of {list(STATUSES)}"),
              (not v.reason, "no reason"),
              (v.status != UNKNOWN and not v.source, f"{v.status} without a source"),
              (v.status in CODE_GROUPED and not v.canonical, f"{v.status} without the canonical name it was screened by"))
    return [f"{n}: {text}" for failed, text in checks if failed]


def validate_screen(verdicts: dict[int, Verdict], items: list[Item]) -> list[str]:
    ids = {i.id for i in items}
    problems = [f"{n}: no verdict" for n in sorted(ids - set(verdicts))]
    problems += [f"{n}: verdict for no item" for n in sorted(set(verdicts) - ids)]
    return problems + [p for n, v in sorted(verdicts.items()) for p in _verdict_problems(n, v)]


def _catalog_problems(catalog) -> list[str]:
    ok = isinstance(catalog, dict) and isinstance(catalog.get("source"), str) and catalog["source"] != "" \
        and isinstance(catalog.get("sha256"), str) and SHA256.fullmatch(catalog["sha256"])
    return [] if ok else [f"catalog {catalog!r} is not {{source, sha256}}"]


def validate_screen_document(doc: dict, items: list[Item]) -> list[str]:
    try:
        verdicts, catalog = read_screen(doc), read_screen_catalog(doc)
    except (KeyError, TypeError, ValueError) as e:
        return [f"screen.json does not parse: {e}"]
    return _catalog_problems(catalog) + validate_screen(verdicts, items)
