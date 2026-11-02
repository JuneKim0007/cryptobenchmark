from __future__ import annotations

from pathlib import Path

from ...data_handler.inbound import RunContext
from ...dto.grouping import items_document, profiles_document
from ...files import write_json
from ...validation import require
from ...validation.grouping.items import validate_items
from ...catalog.families import Families
from ...run_dir import GroupingPaths
from .items import build

INPUTS = ("probe", "trial", "inventory", "prepared", "benchmark")


def build_stage(manifest_path: Path, run: Path, families: Families | None = None) -> GroupingPaths:
    context = RunContext.load(manifest_path, families=families)
    missing = [k for k in INPUTS if context.file(k) is None]
    require(str(manifest_path), [f"files.{k}: absent; the grouping stage needs it" for k in missing])
    items, profiles = build(context.probe, context.names, context.trial, context.inventory, context.prepared,
                            context.benchmark, context.families)
    require("items", validate_items(items, profiles, context.families))
    paths = GroupingPaths(run)
    paths.root.mkdir(parents=True, exist_ok=True)
    write_json(paths.items, items_document(items))
    write_json(paths.profiles, profiles_document(profiles))
    return paths
