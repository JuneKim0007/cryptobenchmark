"""Units applied in one function: each one's own copy of the file with only its splices, so the function is measured
with that unit swapped alone: original, A only, B only; `patched/` holds all of them, whose function would count both."""
from __future__ import annotations

import shutil
from collections import defaultdict

from ...dto.site import Scope
from ...dto.unit import Unit
from ...files import write_text_making_parents
from ...run_dir import AppPaths
from .splice import Splice, apply


def _sharing(applied: dict[str, dict[str, list[Splice]]], units: dict[str, Unit], scopes: dict[str, Scope]) -> set[str]:
    in_function: dict[tuple, set[str]] = defaultdict(set)
    for uid in applied:
        for m in units[uid].members:
            in_function[(scopes[m].file, scopes[m].start, scopes[m].end)].add(uid)
    return {uid for ids in in_function.values() if len(ids) > 1 for uid in ids}


def write_alone(applied: dict[str, dict[str, list[Splice]]], units: list[Unit], scopes: dict[str, Scope],
                text_of: dict[str, str], out: AppPaths) -> None:
    """applied: per unit id, its splices per file; text_of: each edited file's original text."""
    shutil.rmtree(out.alone_root, ignore_errors=True)
    by_id = {u.id: u for u in units}
    for uid in sorted(_sharing(applied, by_id, scopes)):
        for file, splices in applied[uid].items():
            write_text_making_parents(out.alone(uid) / file, apply(text_of[file], splices))
