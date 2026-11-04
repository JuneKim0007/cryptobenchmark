"""The replay's grouping checks: the grouping outbox and knowledge, screen.json and its classify review, worthiness folders."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.evaluate.worthiness.kind import WorthinessKind
from ..ai.parse.algorithm_classify.kind import ClassifyKind
from ..ai.parse.algorithm_classify.state import Classified, candidates
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..dto import Verdicts
from ..dto.classify import read_batches
from ..dto.grouping import read_items
from ..dto.grouping_state import Knowledge
from ..dto.perf_mode import PerfMode
from ..dto.screen import qualified_verdicts
from ..files import read_json, read_yaml
from ..result.evidence import build_evidence
from ..result.modes import mode_of
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.failure import ValidationFailed
from ..validation.screen import validate_model_verdicts, validate_screen_document


def check_worthiness(run: Path, name: str, groups: dict, rows, screen) -> list[str]:
    directory = rd.worthiness(run, name)
    try:
        mode = mode_of(PerfMode.parse(name))
        saved = Verdicts.from_json(read_json(directory / rd.VERDICTS))
    except ValueError as e:
        return [f"{e}; the folder is from before perfMode"]
    measurements = rd.load_measurements(run)
    evidence = build_evidence(groups, rows, measurements.byRow, qualified_verdicts(groups, screen), mode.perf)
    kind = WorthinessKind(mode, measurements.comparability, evidence, directory)
    try:
        records = active_outbox(directory).records()
    except OutboxError as e:
        return [str(e)]
    return kind.validate(saved, records)


def check_grouping(grouping: GroupingPaths) -> list[str]:
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


def check_screen(grouping: GroupingPaths, catalog: Catalog) -> dict[str, list[str]]:
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
