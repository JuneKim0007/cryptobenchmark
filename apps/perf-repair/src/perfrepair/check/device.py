"""The replay's device-level checks: measurements, run log, primitives.tsv, suggestions, used.json, charters, events."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.engine import charter_file
from ..ai.runtime.engine.outbox import FINGERPRINT, OUTBOXES
from ..data_handler.inbound.manifest import read_manifest
from ..data_handler.inbound.primitives import read_primitives
from ..device.primitives import status_of
from cryptobench.catalogue.grouping import read_items
from ..files import read_json, read_yaml
from ..run_dir import GroupingPaths
from ..validation.benchmark_coverage import validate_coverage
from ..validation.bundled import validate_suggestions
from ..validation.events import validate_events
from ..validation.manifest import validate_manifest
from ..validation.measurements import validate_measurements
from ..validation.primitives import validate_primitives
from ..validation.primitives_missing import validate_missing
from ..validation.run_log import validate_run_log
from ..validation.used import validate_used


def check_beside_rows(run: Path, rows) -> dict[str, list[str]]:
    out = {}
    for name, load, check in ((rd.MEASUREMENTS, rd.load_measurements, validate_measurements),
                              (rd.RUN_LOG, rd.load_run_log, validate_run_log)):
        if (run / name).exists():
            doc = parsed(load, run)
            out[name] = [doc] if isinstance(doc, str) else check(doc, rows)
    return out


def check_manifest(run: Path) -> dict[str, list[str]]:
    if not (run / rd.MANIFEST).is_file():
        return {}
    read = parsed(lambda r: read_manifest(r / rd.MANIFEST), run)
    return {rd.MANIFEST: [read] if isinstance(read, str) else validate_manifest(*read)}


def check_details(run: Path) -> dict[str, list[str]]:
    out = {}
    for name, check in ((rd.PRIMITIVES_MISSING, validate_missing), (rd.BENCHMARK_COVERAGE, validate_coverage)):
        if (run / name).is_file():
            doc = parsed(lambda r: read_yaml(r / name), run)
            out[name] = [doc] if isinstance(doc, str) else check(doc)
    return out


def check_primitives(run: Path, rows) -> dict[str, list[str]]:
    if not (run / rd.PRIMITIVES).is_file():
        return {}
    try:
        table, measurements = read_primitives(run), rd.load_measurements(run)
        made_from = status_of(run)
    except (KeyError, TypeError, ValueError) as e:
        return {rd.PRIMITIVES: [f"does not read: {type(e).__name__} {e}"]}
    return {rd.PRIMITIVES: validate_primitives(table, rows, measurements, made_from)}


def check_suggestions(run: Path) -> dict[str, list[str]]:
    path = run / rd.BUNDLED_SUGGESTIONS
    return {rd.BUNDLED_SUGGESTIONS: validate_suggestions(read_yaml(path))} if path.is_file() else {}


def check_used(run: Path, grouping: GroupingPaths) -> dict[str, list[str]]:
    if not (run / rd.USED).is_file():
        return {}
    try:
        used = rd.load_used(run)
    except (KeyError, TypeError, ValueError) as e:
        return {rd.USED: [f"does not read: {type(e).__name__} {e}"]}
    return {rd.USED: validate_used(used, {i.qualified for i in read_items(read_json(grouping.items))})}


def check_charters(run: Path) -> dict[str, list[str]]:
    """Every outbox's charter.json hashes to its folder's name."""
    out = {}
    for directory in sorted(run.rglob(f"{OUTBOXES}/*")):
        if directory.is_dir() and FINGERPRINT.fullmatch(directory.name):
            out[str((directory / rd.CHARTER).relative_to(run))] = charter_file.problems(directory / rd.CHARTER, directory.name)
    return out


def check_events(run: Path) -> dict[str, list[str]]:
    return {rd.EVENTS: validate_events(run / rd.EVENTS)} if (run / rd.EVENTS).is_file() else {}


def parsed(load, run: Path):
    """The loaded document, or the problem a malformed file is."""
    try:
        return load(run)
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as e:
        return f"does not parse: {type(e).__name__} {e}"
