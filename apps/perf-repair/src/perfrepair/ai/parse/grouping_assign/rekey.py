"""One move of an outbox from when records named items by position, its charter inputs the screened-out ids, to one that
names them by Item.key: nothing is asked again."""
from __future__ import annotations

import logging
from dataclasses import replace

from ....log import step
from ....run_dir import GroupingPaths
from ....screen.groups import screened_out
from ...runtime.engine.outbox import active_outbox, carry
from ...runtime.prompt import PromptLibrary
from .kind import GroupingKind, charter

LOG = logging.getLogger(__name__)


def _positional_inputs(kind: GroupingKind) -> str:
    return "\n".join(str(k) for k, v in sorted((kind.screen or {}).items()) if screened_out(v))


def rekey(paths: GroupingPaths, library: PromptLibrary) -> bool:
    """The old charter hashing to the outbox's name vouches for the prompts and the screened-out positions; otherwise the
    ids may have moved, so the records are left behind and their items are asked."""
    outbox = active_outbox(paths.root)
    records = outbox.records()
    if not records or not all(r.item.isdigit() for r in records):
        return False
    kind = GroupingKind(paths)
    if charter(library, _positional_inputs(kind)).fingerprint != outbox.fingerprint or any(
            int(r.item) not in kind.by_id for r in records):
        LOG.warning("outbox_not_rekeyed: %s names items by a position that may have moved; its items are asked again",
                    outbox.fingerprint)
        return False
    with step("grouping", "rekey", detail=outbox.fingerprint) as s:
        carry(paths.root, charter(library), [replace(r, item=kind.by_id[int(r.item)].key) for r in records])
        s.count(records=len(records))
    return True
