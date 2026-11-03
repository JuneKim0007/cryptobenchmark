"""What the device's grouping knowledge covers, computed each run from the active outbox, never a stored flag; noRerun's reader."""
from __future__ import annotations

from dataclasses import dataclass

from ..ai.parse.grouping_assign.kind import GroupingKind
from ..ai.runtime.engine.outbox import active_outbox
from ..config.load import Loaded
from ..files import json_text
from ..grouping.report.checks import report_documents
from ..inputs.table import GROUPING_NO_RERUN
from ..run_dir import GroupingPaths



@dataclass(frozen=True)
class Coverage:
    """pending: non-screened-out items with no record, a dropped one being decided; current: the saved files are what the
    outbox and today's items make."""
    asked: int
    pending: tuple[str, ...]
    current: bool


def _current(paths: GroupingPaths) -> bool:
    return all(path.is_file() and path.read_text() == json_text(doc) for path, doc in report_documents(paths).items())


def coverage(paths: GroupingPaths) -> Coverage:
    kind = GroupingKind(paths)
    done = {r.item for r in active_outbox(paths.root).records()}
    asked = kind.pending()
    pending = tuple(kind.label(i) for i in asked if i.key not in done)
    return Coverage(len(asked), pending, not pending and _current(paths))


def no_rerun(settings: Loaded | None) -> bool:
    """False asks every item again; knowledge that is missing is asked either way."""
    if settings is None:
        return True
    return settings.read(GROUPING_NO_RERUN)
