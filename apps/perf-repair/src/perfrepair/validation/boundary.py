"""One algorithm keeps one identity across the stages: results, compacted rows, device items, catalogs. Absent files are skipped."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from cryptobench.paths import GroupingTree, RunTree
from cryptobench.catalogue.groups import group_catalog
from ..catalog.identity import case_id_pattern, resolve
from cryptobench.catalogue.names import Names
from ..catalog.types import types as type_catalog
from ..data_handler.inbound.manifest import read_manifest
from cryptobench.catalogue.grouping import SEPARATOR, qualified
from ..files import read_json
from .finding import ADVISORY, BLOCKING, Violation

EVIDENCE = 8


def _found(invariant: str, severity: str, subject: str, lines: list[str], fix: str) -> list[Violation]:
    shown = sorted(set(lines))
    more = [f"and {len(shown) - EVIDENCE} more"] * (len(shown) > EVIDENCE)
    return [Violation(invariant, severity, subject, (*shown[:EVIDENCE], *more), fix)] if shown else []


def _rows(device: Path) -> list[dict]:
    rows = read_json(RunTree(device).rows)["rows"] if (RunTree(device).rows).is_file() else []
    return [r for r in rows if "rowId" in r]


def _results_cases(device: Path) -> list[dict] | None:
    if not (RunTree(device).manifest).is_file():
        return None
    manifest, base = read_manifest(RunTree(device).manifest)
    path = base / manifest.files["benchmark"] if manifest.files.get("benchmark") else None
    return read_json(path).get("cases") or [] if path and path.is_file() else None


def case_ids_read_back(rows: list[dict]) -> list[Violation]:
    bad = [r["rowId"] for r in rows if not case_id_pattern(r).match(r["rowId"])]
    return _found("case_id_reads_back", BLOCKING, "rows.json", bad, "the row's fields and its id came from different cases")


def ids_agree(device: Path, rows: list[dict]) -> list[Violation]:
    """Results, rows and measurements hold one set of ids."""
    ids, found = {r["rowId"] for r in rows}, []
    repeated = [i for i, n in Counter(r["rowId"] for r in rows).items() if n > 1]
    found += _found("case_ids_unique", BLOCKING, "rows.json", repeated, "two rows share an id")
    if rows and (RunTree(device).measurements).is_file():
        keys = set(read_json(RunTree(device).measurements)["measurements"])
        found += _found("ids_agree", BLOCKING, "measurements.json", [f"{i}: only one side" for i in ids ^ keys], "rebuild rows and measurements together")
    cases = _results_cases(device)
    if rows and cases is not None:
        found += _found("ids_agree", BLOCKING, "benchmark.json", [f"{i}: only one side" for i in ids ^ {c["id"] for c in cases}], "rebuild rows from these results")
    return found


def compaction_keeps_rows_apart(rows: list[dict]) -> list[Violation]:
    """Rows that land in one cell of primitives.tsv lose one of them; its key has no parameters."""
    cells = Counter((r["type"], r["algorithm"], r["provider"], r["operation"], r.get("keySize"), r.get("phase"), r.get("variant"),
                     r.get("inputSize")) for r in rows)
    return _found("primitives_cell_is_one_row", BLOCKING, "primitives.tsv", [str(k) for k, n in cells.items() if n > 1],
                  "two parameter sets share a cell; add the parameters to the table's key")


def measured_cases_are_items(rows: list[dict], items: set[str]) -> list[Violation]:
    lost = [q for q in (qualified(r["type"], r["algorithm"], r["provider"]) for r in rows) if q not in items]
    return _found("measured_case_is_an_item", BLOCKING, "rows.json", lost, "rebuild grouping from this probe and these results")


def names_parse(items: list[dict]) -> list[Violation]:
    bad = [f"{i['type']} {i['name']} {i['provider']}" for i in items
           if any(SEPARATOR in str(i[k]) for k in ("type", "name", "provider"))]
    return _found("item_id_parses", BLOCKING, "items.json", bad, f"a registered name holds {SEPARATOR!r}: an id cannot be read back")


def catalogs_agree(items: list[dict], verdicts: dict[str, dict], names: Names) -> list[Violation]:
    """Screening's canonical name against the names catalog, and each named algorithm's place in a group and the types."""
    conflict, unlisted, untyped = [], [], []
    catalog, types = group_catalog(), type_catalog()
    for i in items:
        said = (verdicts.get(str(i["id"])) or {}).get("canonical")
        mine = resolve(i["type"], i["name"], i["provider"], i["family"], names)
        if said != mine.canonical:
            conflict.append(f"{mine.item}: screening {said}, names catalog {mine.canonical}")
        listed = {a for g in catalog.families if g.family == i["family"] for a in g.algorithms}
        if said and said not in listed:
            unlisted.append(f"{i['family']} {said}")
        elif said and types.of(i["family"], said) is None:
            untyped.append(f"{i['family']} {said}")
    return (_found("names_agree", ADVISORY, "catalogs", conflict, "settle the name in screening.yaml or algorithm-names.yaml")
            + _found("name_is_in_its_group", ADVISORY, "catalogs", unlisted, "add it to algorithms/groups.yaml")
            + _found("name_has_facts", ADVISORY, "catalogs", untyped, "add its type facts to its algorithms/ entry"))


def used_items_exist(device: Path, rows: list[dict], items: set[str]) -> list[Violation]:
    if not (RunTree(device).used).is_file():
        return []
    used = [u["item"] for u in read_json(RunTree(device).used)["items"]]
    found = _found("used_is_an_item", BLOCKING, "used.json", [u for u in used if u not in items], "rebuild the used set from this grouping")
    if rows:
        measured = {qualified(r["type"], r["algorithm"], r["provider"]) for r in rows}
        found += _found("used_is_measured", ADVISORY, "used.json", [u for u in used if u in items and u not in measured],
                        "a used item with no measurement has no options; measure it or report why not")
    return found


def stage_violations(device: Path, names: Names | None = None) -> list[Violation]:
    """What the guide's gate checks: the ids of one stage against the next."""
    device, paths = Path(device), GroupingTree(device)
    rows = _rows(device)
    found = ids_agree(device, rows) + compaction_keeps_rows_apart(rows)
    if not paths.items.is_file():
        return found
    items = read_json(paths.items)["items"]
    keys = {qualified(i["type"], i["name"], i["provider"]) for i in items}
    found += names_parse(items) + measured_cases_are_items(rows, keys) + used_items_exist(device, rows, keys)
    if paths.screen.is_file():
        found += catalogs_agree(items, read_json(paths.screen)["verdicts"], names or Names.load())
    return found


def boundary_violations(device: Path, names: Names | None = None) -> list[Violation]:
    """The command's whole check: also each case id against its fields, a rule that changes with the case id itself (#111)."""
    return case_ids_read_back(_rows(Path(device))) + stage_violations(device, names)
