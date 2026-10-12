"""Stage: a finished grouping → checks.json and groups.json, each validated before it is written."""
from __future__ import annotations

from ...dto.grouping import read_items, read_profiles
from ...dto.grouping_output import checks_document
from ...dto.grouping_state import Knowledge
from ...files import read_json, write_json
from ...validation import require
from ...validation.grouping.knowledge import validate_knowledge
from ...validation.grouping.output import validate_output
from ..catalog.families import Families
from ..paths import GroupingPaths
from ..state.cursor import cursor
from ..state.outbox import Outbox
from .output import assemble
from .rules import check


def report(paths: GroupingPaths, families: Families | None = None) -> dict:
    families = families or Families.load()
    items = {i.id: i for i in read_items(read_json(paths.items))}
    profiles = read_profiles(read_json(paths.profiles))
    records = Outbox(paths.outbox).open().records()
    knowledge = Knowledge.from_json(read_json(paths.knowledge))
    require("knowledge", validate_knowledge(knowledge, records, items, families))
    unfinished = cursor(list(items.values()), records).next
    require("grouping", [] if unfinished is None else [f"item {unfinished} is not decided yet; run assign first"])
    findings = check(knowledge, items, profiles)
    write_json(paths.checks, checks_document(findings))
    document = assemble(knowledge, items, profiles, findings, records, families)
    require("groups.json", validate_output(document, items))
    write_json(paths.groups, document)
    return document
