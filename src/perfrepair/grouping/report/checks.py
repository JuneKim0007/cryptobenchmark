"""Stage: a finished grouping → checks.json and groups.json, each validated before it is written; and the
one validated reader of groups.json for whatever consumes it."""
from __future__ import annotations

from ...dto.grouping import read_items
from ...dto.grouping_output import checks_document
from ...files import read_json, write_json
from ...orchestrate.engine.kind import project
from ...orchestrate.engine.outbox import Outbox
from ...validation import require
from ...validation.grouping.output import validate_output
from ..catalog.families import Families
from ..kind import GroupingKind
from ..paths import GroupingPaths
from ..state.cursor import cursor
from .output import assemble
from .rules import check


def report(paths: GroupingPaths, families: Families | None = None) -> dict:
    kind = GroupingKind(paths, families)
    records = Outbox(paths.outbox).open().records()
    knowledge = project(kind, records)
    require("grouping", kind.validate(knowledge, records))
    unfinished = cursor(kind.items(), records).next
    require("grouping", [] if unfinished is None else [f"item {unfinished} is not decided yet; run assign first"])
    findings = check(knowledge, kind.by_id, kind.profiles)
    write_json(paths.checks, checks_document(findings))
    document = assemble(knowledge, kind.by_id, kind.profiles, findings, records, kind.families)
    require("groups.json", validate_output(document, kind.by_id))
    write_json(paths.groups, document)
    return document


def read_groups(paths: GroupingPaths) -> dict:
    """groups.json, validated against items.json; a consumer never reads it any other way."""
    document = read_json(paths.groups)
    require("groups.json", validate_output(document, {i.id: i for i in read_items(read_json(paths.items))}))
    return document
