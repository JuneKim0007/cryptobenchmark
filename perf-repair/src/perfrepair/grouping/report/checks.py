from __future__ import annotations

from pathlib import Path

from ...dto.grouping_output import checks_document
from ...files import write_json
from ...log import step
from ...ai.runtime.engine.kind import project
from ...ai.runtime.engine.outbox import active_outbox
from ...validation import require
from ...validation.grouping.output import validate_output
from ...catalog.families import Families
from ...ai.parse.grouping_assign.kind import GroupingKind
from ...run_dir import GroupingPaths
from ...ai.parse.grouping_assign.state import cursor
from ..interop_read import imported
from .output import assemble
from .rules import check, check_interop


def report(paths: GroupingPaths, families: Families | None = None) -> dict:
    with step("grouping", "report") as s:
        document = _report(paths, families)
        s.count(groups=len(document["groups"]), dropped=len(document["dropped"]))
        s.wrote(paths.checks, paths.groups)
    return document


def _report(paths: GroupingPaths, families: Families | None) -> dict:
    documents = report_documents(paths, families)
    for path, doc in documents.items():
        write_json(path, doc)
    return documents[paths.groups]


def report_documents(paths: GroupingPaths, families: Families | None = None) -> dict[Path, dict]:
    """What the finished grouping's files should hold, the outbox being the commit; nothing written."""
    kind = GroupingKind(paths, families)
    records = active_outbox(paths.root).records()
    knowledge = project(kind, records)
    require("grouping", kind.validate(knowledge, records))
    unfinished = cursor(kind.pending(), records).next
    require("grouping", [] if unfinished is None else [f"item {unfinished} is not decided yet; run assign first"])
    interop = imported(paths)
    findings = check(knowledge, kind.by_id, kind.profiles) + check_interop(interop, kind.by_id)
    document = assemble(knowledge, kind.by_id, kind.profiles, findings, records, kind.families, interop, kind.screen)
    require("groups.json", validate_output(document, kind.by_id, kind.screen, kind.profiles))
    return {paths.knowledge: knowledge.to_json(), paths.checks: checks_document(findings), paths.groups: document}
