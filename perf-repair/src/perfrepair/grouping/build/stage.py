from __future__ import annotations

from pathlib import Path

from ...data_handler.inbound import RunContext
from ...dto.grouping import items_document, profiles_document
from ...dto.screen import screen_document
from ...files import json_text, sha256_text, write_texts
from ...validation import require, validate_screen
from ...validation.grouping.items import validate_items
from ...catalog.families import Families
from ...run_dir import GroupingPaths
from ...screen.catalog import Catalog, screening_catalog
from ...screen.evidence import batches, unknown_evidence
from ...screen.stage import screen_items
from ...ai.parse.algorithm_classify.command import Reviewer, classify
from .items import build

INPUTS = ("probe", "trial", "inventory", "prepared", "benchmark")


def build_stage(manifest_path: Path, run: Path, catalog: Catalog | None = None, reviewer: Reviewer | None = None,
                families: Families | None = None, echo=print) -> GroupingPaths:
    """reviewer: given only with screening.aiReview; it classifies the unknown items before screen.json is written."""
    catalog = catalog or screening_catalog(None)
    context = RunContext.load(manifest_path, families=families, screening=catalog.screening)
    missing = [k for k in INPUTS if context.file(k) is None]
    require(str(manifest_path), [f"files.{k}: absent; the grouping stage needs it" for k in missing])
    items, profiles = build(context.probe, context.names, context.trial, context.inventory, context.prepared,
                            context.benchmark, context.families)
    require("items", validate_items(items, profiles, context.families))
    verdicts = screen_items(context, items)
    require("screen", validate_screen(verdicts, items))
    paths = GroupingPaths(run)
    paths.root.mkdir(parents=True, exist_ok=True)
    review = None
    if reviewer is not None:
        verdicts, review = classify(paths, batches(unknown_evidence(context, items, verdicts)), verdicts, reviewer, echo)
        require("screen", validate_screen(verdicts, items))
    items_text, profiles_text = json_text(items_document(items)), json_text(profiles_document(profiles))
    built = {"items": sha256_text(items_text), "profiles": sha256_text(profiles_text)}
    # screen.json first: its absence reads as "built without screening"; any later partial rename fails its digests
    write_texts([(paths.screen, json_text(screen_document(verdicts, catalog.identity(), built, review))),
                 (paths.profiles, profiles_text), (paths.items, items_text)])
    return paths
