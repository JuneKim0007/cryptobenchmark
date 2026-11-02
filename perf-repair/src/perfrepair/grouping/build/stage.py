from __future__ import annotations

from pathlib import Path

from ...data_handler.inbound import RunContext
from ...dto.grouping import items_document, profiles_document
from ...dto.screen import screen_document
from ...files import write_json
from ...validation import require, validate_screen
from ...validation.grouping.items import validate_items
from ...catalog.families import Families
from ...run_dir import GroupingPaths
from ...screen.catalog import Catalog, screening_catalog
from ...screen.stage import screen_items
from .items import build

INPUTS = ("probe", "trial", "inventory", "prepared", "benchmark")


def build_stage(manifest_path: Path, run: Path, catalog: Catalog | None = None,
                families: Families | None = None) -> GroupingPaths:
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
    write_json(paths.items, items_document(items))
    write_json(paths.profiles, profiles_document(profiles))
    write_json(paths.screen, screen_document(verdicts, catalog.identity()))
    return paths
