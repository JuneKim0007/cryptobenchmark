"""The replay's grouping checks: the grouping outbox and knowledge, screen.json and its classify review."""
from __future__ import annotations


import yaml

from cryptobench.paths import GroupingTree
from .. import run_dir as rd
from ..ai.parse.algorithm_classify.kind import ClassifyKind
from ..ai.parse.algorithm_classify.state import Classified, candidates
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..ai.runtime.engine.kind import rebuild_problems
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..dto.classify import read_batches
from cryptobench.catalogue.grouping import read_items
from ..dto.grouping_state import Knowledge
from ..files import read_json
from ..screen.catalog import Catalog
from ..validation.failure import ValidationFailed
from ..validation.screen import validate_model_verdicts, validate_screen_document


def check_grouping(grouping: GroupingTree) -> list[str]:
    try:
        outbox = active_outbox(grouping.root)
        records = outbox.records()
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
    # with nothing asked, `grouping report` alone writes knowledge.json: no outbox to rebuild from
    return kind.validate(saved, records) + ([] if outbox.fingerprint is None else rebuild_problems(kind, records))


def check_screen(grouping: GroupingTree, catalog: Catalog) -> dict[str, list[str]]:
    if not grouping.screen.exists():
        return {}
    items, doc = read_items(read_json(grouping.items)), read_json(grouping.screen)
    problems = validate_screen_document(doc, items, rd.built(grouping))
    if problems:
        return {"grouping/screen.json": problems}
    return {"grouping/screen.json": catalog.mismatch(rd.load_screen_catalog(grouping))} | _classify(grouping)


def _classify(grouping: GroupingTree) -> dict[str, list[str]]:
    review = rd.load_screen_review(grouping)
    if review is None:
        return {}
    try:
        batches = read_batches(read_json(grouping.classify_batches))
        outbox = active_outbox(grouping.classify)
        records = outbox.records()
        saved = Classified.from_json(read_json(grouping.classified))
        proposals = grouping.registry_candidates.read_text()
    except (OSError, KeyError, TypeError, ValueError) as e:
        return {"grouping/classify": [f"does not read: {e}"]}
    problems = [] if outbox.fingerprint == review else [
        f"screen.json was reviewed under {review}, the active classify outbox is {outbox.fingerprint}"]
    kind = ClassifyKind(batches, grouping)
    problems += kind.validate(saved, records) + rebuild_problems(kind, records)
    problems += validate_model_verdicts(rd.load_screen(grouping), saved.answers, review)
    if proposals != yaml.safe_dump(candidates(saved, batches, review), sort_keys=False):
        problems.append(f"{grouping.registry_candidates.name} differs from the accepted answers")
    return {"grouping/classify": problems}
