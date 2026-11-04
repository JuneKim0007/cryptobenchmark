"""seen(): what a device folder holds now, for the plan to compare with device.yaml."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..data_handler.inbound import read_manifest
from ..files import sha256_file
from ..run_dir import GroupingPaths
from .plan import Seen
from .primitives import inputs as primitive_inputs
from .primitives import unusable


def _inbound(folder: Path) -> str | None:
    missing = [f for f in (rd.ROWS, rd.MEASUREMENTS, rd.RUN_LOG) if not (folder / f).is_file()]
    if missing:
        return f"{missing[0]} missing"
    for name, load in ((rd.ROWS, rd.load_rows), (rd.MEASUREMENTS, rd.load_measurements)):
        try:
            load(folder)
        except (ValueError, KeyError, TypeError) as e:
            return f"{name} unreadable ({e})"
    return None


def seen(folder: Path) -> Seen:
    manifest = read_manifest(folder / rd.MANIFEST)[0] if (folder / rd.MANIFEST).is_file() else None
    record, problem = rd.load_device_record(folder)
    grouping = GroupingPaths(folder)
    return Seen(manifest, sha256_file(folder / rd.MANIFEST), record, problem,
                inbound=_inbound(folder),
                grouping=all(p.is_file() for p in (grouping.items, grouping.profiles, grouping.screen)),
                primitives=unusable(folder), made_from=primitive_inputs(folder))
