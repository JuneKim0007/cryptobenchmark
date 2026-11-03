from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto import Verdicts
from ..dto.grouping import read_items
from ..dto.screen import Verdict, qualified_verdicts
from ..dto.grouping_state import Knowledge
from ..dto.site import Scope
from ..dto.classify import read_batches
from ..files import read_json, read_yaml
from ..ai.parse.algorithm_classify.kind import ClassifyKind
from ..ai.parse.algorithm_classify.state import Classified, candidates
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..ai.evaluate.worthiness.kind import WorthinessKind
from ..ai.runtime.engine import charter_file
from ..ai.runtime.engine.outbox import FINGERPRINT, OUTBOXES, OutboxError, active_outbox
from ..result.evidence import build_evidence
from ..result.modes import MODES
from ..validation.dossiers import validate_dossiers
from ..validation.events import validate_events
from ..validation.app import validate_app_dir
from ..validation.failure import ValidationFailed
from ..validation.grouping.interop import validate_interop
from ..validation.measurements import validate_measurements
from ..validation.report import validate_report, validate_summary
from ..validation.rows import validate_rows
from ..validation.run_log import validate_run_log
from ..validation.screen import validate_model_verdicts, validate_screen_document


def validate_run(run: Path, catalog: Catalog) -> dict[str, list[str]]:
    run, out = Path(run), {}
    if not (run / rd.ROWS).is_file():
        return {rd.ROWS: [f"missing: {run / rd.ROWS}"]}
    rows = _parsed(rd.load_rows, run)
    if isinstance(rows, str):
        return {rd.ROWS: [rows]}
    out[rd.ROWS] = validate_rows(rows)
    out |= _beside_rows(run, rows)
    out |= _charters(run) | _events(run)
    reports = []
    for directory in rd.app_dirs(run):
        out |= validate_app_dir(directory)
        if (directory / rd.REPORT).is_file():
            reports.append(read_json(directory / rd.REPORT))
            out[f"{directory.name}/{rd.REPORT}"] = validate_report(reports[-1], directory.name)
    if (run / rd.SUMMARY).is_file():
        out[rd.SUMMARY] = validate_summary(read_json(run / rd.SUMMARY), reports)
    grouping = GroupingPaths(run)
    if grouping.items.exists():
        out["grouping"] = _grouping(grouping)
        out |= _screen(grouping, catalog)
    if not grouping.groups.exists():
        return out
    try:
        groups = read_groups(grouping)
        out["grouping/groups.json"] = []
    except ValidationFailed as e:
        out["grouping/groups.json"] = e.problems
        return out
    out |= validate_interop(groups, grouping.interop_plan, grouping.interop)
    screen = rd.load_screen(grouping)
    out |= _dossiers(run, groups, screen, catalog)
    for mode in MODES.values():
        directory = rd.worthiness(run, mode.name)
        if (directory / rd.VERDICTS).exists():
            measurements = rd.load_measurements(run)
            evidence = build_evidence(groups, rows, measurements.byRow, qualified_verdicts(groups, screen))
            kind = WorthinessKind(mode, measurements.comparability, evidence, directory)
            try:
                records = active_outbox(directory).records()
            except OutboxError as e:
                out[directory.name] = [str(e)]
                continue
            saved = Verdicts.from_json(read_json(directory / rd.VERDICTS))
            out[directory.name] = kind.validate(saved, records)
    return out


def _beside_rows(run: Path, rows) -> dict[str, list[str]]:
    out = {}
    for name, load, check in ((rd.MEASUREMENTS, rd.load_measurements, validate_measurements),
                              (rd.RUN_LOG, rd.load_run_log, validate_run_log)):
        if (run / name).exists():
            doc = _parsed(load, run)
            out[name] = [doc] if isinstance(doc, str) else check(doc, rows)
    return out


def _charters(run: Path) -> dict[str, list[str]]:
    """Every outbox's charter.json hashes to its folder's name; a supervisor review's to the charter it names."""
    out = {}
    for directory in sorted(run.rglob(f"{OUTBOXES}/*")):
        if directory.is_dir() and FINGERPRINT.fullmatch(directory.name):
            out[str((directory / rd.CHARTER).relative_to(run))] = charter_file.problems(directory / rd.CHARTER, directory.name)
    grouping = GroupingPaths(run)
    if grouping.supervisor.is_file():
        out[str(grouping.supervisor_charter.relative_to(run))] = charter_file.problems(
            grouping.supervisor_charter, read_json(grouping.supervisor).get("charter"))
    return out


def _events(run: Path) -> dict[str, list[str]]:
    return {rd.EVENTS: validate_events(run / rd.EVENTS)} if (run / rd.EVENTS).is_file() else {}


def _parsed(load, run: Path):
    """The loaded document, or the problem a malformed file is."""
    try:
        return load(run)
    except (KeyError, TypeError, ValueError) as e:
        return f"does not parse: {type(e).__name__} {e}"


def _dossiers(run: Path, groups: dict, screen: dict[int, Verdict] | None, catalog: Catalog) -> dict[str, list[str]]:
    out, handler = {}, catalog.handler()
    for directory in sorted(run.glob(f"*/{rd.DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in read_json(directory.parent / rd.SCOPES)["scopes"]]
        verdicts = handler.app_verdicts(groups, screen, read_json(directory.parent / rd.APP).get("targetSdk"))
        out[str(directory.relative_to(run))] = validate_dossiers(read_json(directory), scopes, groups, verdicts)
    return out


def _grouping(grouping: GroupingPaths) -> list[str]:
    try:
        records = active_outbox(grouping.root).records()
    except OutboxError as e:
        return [str(e)]
    if not grouping.knowledge.exists():
        return [f"{grouping.knowledge.name} missing for {len(records)} committed records"] if records else []
    try:
        saved = Knowledge.from_json(read_json(grouping.knowledge))
    except (KeyError, TypeError, ValueError) as e:
        return [f"{grouping.knowledge.name} does not parse: {e}"]
    try:
        kind = GroupingKind(grouping)
    except ValidationFailed as e:
        return e.problems
    return kind.validate(saved, records)


def _screen(grouping: GroupingPaths, catalog: Catalog) -> dict[str, list[str]]:
    if not grouping.screen.exists():
        return {}
    items, doc = read_items(read_json(grouping.items)), read_json(grouping.screen)
    problems = validate_screen_document(doc, items, rd.built(grouping))
    if problems:
        return {"grouping/screen.json": problems}
    return {"grouping/screen.json": catalog.mismatch(rd.load_screen_catalog(grouping))} | _classify(grouping)


def _classify(grouping: GroupingPaths) -> dict[str, list[str]]:
    review = rd.load_screen_review(grouping)
    if review is None:
        return {}
    try:
        batches = read_batches(read_json(grouping.classify_batches))
        outbox = active_outbox(grouping.classify)
        records = outbox.records()
        saved = Classified.from_json(read_json(grouping.classified))
        proposals = read_yaml(grouping.registry_candidates)
    except (OSError, KeyError, TypeError, ValueError) as e:
        return {"grouping/classify": [f"does not read: {e}"]}
    problems = [] if outbox.fingerprint == review else [
        f"screen.json was reviewed under {review}, the active classify outbox is {outbox.fingerprint}"]
    problems += ClassifyKind(batches, grouping).validate(saved, records)
    problems += validate_model_verdicts(rd.load_screen(grouping), saved.answers, review)
    if proposals != candidates(saved, batches, review):
        problems.append(f"{grouping.registry_candidates.name} differs from the accepted answers")
    return {"grouping/classify": problems}
