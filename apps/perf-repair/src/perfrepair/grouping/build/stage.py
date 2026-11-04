from __future__ import annotations

from collections import Counter
from pathlib import Path

from ...data_handler.inbound import RunContext
from ...dto.grouping import items_document, profiles_document
from ...dto.screen import CODE_GROUPED, screen_document
from ...files import json_text, sha256_text, write_texts
from ...log import step
from ...validation import require, validate_screen
from ...validation.grouping.items import validate_items
from ...catalog.families import Families
from ...run_dir import GroupingPaths
from ...screen.catalog import Catalog
from ...screen.groups import grouped_by_code
from ...screen.evidence import batches, unknown_evidence
from ...screen.stage import screen_items
from ...ai.parse.algorithm_classify.command import Reviewer, classify
from .items import build

INPUTS = ("probe", "trial")
OPTIONAL = ("inventory", "prepared", "benchmark")


def build_stage(manifest_path: Path, run: Path, catalog: Catalog, reviewer: Reviewer | None = None,
                families: Families | None = None, echo=print) -> GroupingPaths:
    """reviewer: given only with device.screening.aiReview; it classifies the unknown items before screen.json is written."""
    with step("grouping", "build") as s:
        paths, items, verdicts, profiles = _build(manifest_path, run, catalog, reviewer, families, echo)
        s.count(items=len(items), verdicts=len(verdicts),
                codeGrouped=sum(1 for v in verdicts.values() if v.status in CODE_GROUPED),
                signatureGrouped=sum(1 for i in items if grouped_by_code(i.id, verdicts, profiles)
                                     and verdicts[i.id].status not in CODE_GROUPED))
        s.wrote(paths.screen, paths.profiles, paths.items)
    return paths


def _screened(context: RunContext, items, profiles, catalog: Catalog) -> dict:
    with step("screening", "screen", detail=f"catalog {catalog.source}") as s:
        verdicts = screen_items(context, items, profiles)
        s.count(**dict(sorted(Counter(v.status for v in verdicts.values()).items())))
    return verdicts


def _build(manifest_path: Path, run: Path, catalog: Catalog, reviewer: Reviewer | None, families: Families | None,
           echo) -> tuple[GroupingPaths, list, dict, dict]:
    context = RunContext.load(manifest_path, families=families, screening=catalog.screening)
    missing = [k for k in INPUTS if context.file(k) is None]
    require(str(manifest_path), [f"files.{k}: absent; the grouping stage needs it" for k in missing])
    present = {k: getattr(context, k) for k in OPTIONAL if context.file(k) is not None}
    items, profiles = build(context.probe, context.names, context.trial, context.families, **present)
    require("items", validate_items(items, profiles, context.families))
    verdicts = _screened(context, items, profiles, catalog)
    require("screen", validate_screen(verdicts, items))
    paths = GroupingPaths(run)
    paths.root.mkdir(parents=True, exist_ok=True)
    review = None
    if reviewer is not None:
        verdicts, review = classify(paths, batches(unknown_evidence(context, items, verdicts)), verdicts, reviewer, echo)
        require("screen", validate_screen(verdicts, items, review))
    items_text, profiles_text = json_text(items_document(items)), json_text(profiles_document(profiles))
    built = {"items": sha256_text(items_text), "profiles": sha256_text(profiles_text)}
    # screen.json first: its absence reads as "built without screening"; any later partial rename fails its digests
    write_texts([(paths.screen, json_text(screen_document(verdicts, catalog.identity(), built, review))),
                 (paths.profiles, profiles_text), (paths.items, items_text)])
    return paths, items, verdicts, profiles
