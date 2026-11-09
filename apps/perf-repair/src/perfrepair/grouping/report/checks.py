from __future__ import annotations

from pathlib import Path

import yaml

from cryptobench.paths import GroupingTree
from ...dto.grouping_output import checks_document
from ...files import write_json, write_text
from ...log import step
from ...ai.runtime.engine.kind import project
from ...ai.runtime.engine.outbox import active_outbox
from ...validation import require
from ...validation.grouping.output import validate_output
from cryptobench.catalogue.families import Families
from ...ai.parse.grouping_assign.kind import GroupingKind
from ...ai.parse.grouping_assign.state import cursor
from ..interop_read import imported
from .candidates import candidates
from .output import assemble
from .rules import check, check_interop


def report(paths: GroupingTree, families: Families | None = None) -> dict:
    with step("grouping", "report") as s:
        document = _report(paths, families)
        s.count(groups=len(document["groups"]), dropped=len(document["dropped"]))
        s.wrote(paths.checks, paths.groups, paths.group_candidates)
    return document


def _report(paths: GroupingTree, families: Families | None) -> dict:
    kind, records, knowledge, findings, documents = _finished(paths, families)
    for path, doc in documents.items():
        write_json(path, doc)
    # a person promotes a row by hand: nothing at run time writes the catalog
    found = candidates(kind, knowledge, records, findings, active_outbox(paths.root).fingerprint, paths.group_candidates)
    write_text(paths.group_candidates, yaml.safe_dump(found, sort_keys=False, width=200))
    return documents[paths.groups]


def report_documents(paths: GroupingTree, families: Families | None = None) -> dict[Path, dict]:
    """What the finished grouping's files should hold, the outbox being the commit; nothing written."""
    return _finished(paths, families)[-1]


def _finished(paths: GroupingTree, families: Families | None):
    kind = GroupingKind(paths, families)
    records = active_outbox(paths.root).records()
    knowledge = project(kind, records)
    require("grouping", kind.validate(knowledge, records))
    unfinished = cursor(kind.pending(), records).next
    require("grouping", [] if unfinished is None else [f"item {unfinished} is not decided yet; run assign first"])
    interop = imported(paths)
    findings = check(knowledge, kind.by_id, kind.profiles) + check_interop(interop, kind.by_id)
    document = assemble(knowledge, kind.by_id, kind.profiles, findings, records, kind.families, interop, kind.screen)
    if kind.scope is not None:
        document["notUsed"] = [i.id for i in kind.not_used(records)]
    require("groups.json", validate_output(document, kind.by_id, kind.screen, kind.profiles))
    return kind, records, knowledge, findings, {paths.knowledge: knowledge.to_json(), paths.checks: checks_document(findings),
                                                paths.groups: document}
