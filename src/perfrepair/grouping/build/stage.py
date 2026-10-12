"""Stage: a benchmark manifest → <run>/grouping/items.json and profiles.json, validated before writing."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from ...data_handler.inbound.manifest import manifest_file, read_manifest
from ...dto.grouping import items_document, profiles_document
from ...files import write_json
from ...validation import require
from ...validation.grouping.items import validate_items
from ..catalog.families import Families
from ..paths import GroupingPaths
from .items import build

INPUTS = ("probe", "trial", "inventory", "prepared", "benchmark")


def _load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())


def build_stage(manifest_path: Path, run: Path, families: Families | None = None) -> GroupingPaths:
    families = families or Families.load()
    manifest, base = read_manifest(manifest_path)
    missing = [k for k in INPUTS if manifest_file(manifest, base, k) is None]
    require(str(manifest_path), [f"files.{k}: absent; the grouping stage needs it" for k in missing])
    documents = {k: _load(manifest_file(manifest, base, k)) for k in INPUTS}
    items, profiles = build(families=families, **documents)
    require("items", validate_items(items, profiles, families))
    paths = GroupingPaths(run)
    paths.root.mkdir(parents=True, exist_ok=True)
    write_json(paths.items, items_document(items))
    write_json(paths.profiles, profiles_document(profiles))
    return paths
