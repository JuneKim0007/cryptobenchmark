import re

import pytest
from grouping_data import BENCHMARK, FAMILIES, INVENTORY, PREPARED, PROBE, TRIAL

from perfrepair.dto.grouping import items_document, profiles_document
from perfrepair.files import write_json
from perfrepair.grouping.build.items import build
from perfrepair.ai.parse.grouping_assign.kind import charter
from perfrepair.grouping.paths import GroupingPaths

from helpers import LIBRARY, QUIET  # noqa: F401  (re-exported for grouping tests)

CHARTER = charter(LIBRARY)


@pytest.fixture
def paths(tmp_path):
    items, profiles = build(PROBE, TRIAL, INVENTORY, PREPARED, BENCHMARK, FAMILIES)
    p = GroupingPaths(tmp_path)
    p.root.mkdir()
    write_json(p.items, items_document(items))
    write_json(p.profiles, profiles_document(profiles))
    return p


def item_name(task):
    return re.search(r"id \d+ · \S+ · (\S+) · (\S+)", task.text).group(1)


def by_name(task, *_):
    name, message = item_name(task), task.text
    for line in message.splitlines():
        m = re.match(r"\s+(\S+) \(\d+ members\)", line)
        if m:
            following = message.split(line, 1)[1].splitlines()[1]
            if f"{name} @" in following:
                return {"group": m.group(1), "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"}
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return {"group": "", "newGroup": {"id": slug, "description": f"the function {name}"}, "amend": [], "reason": "new"}


class Remembering:

    def __init__(self, decide):
        self.decide, self.first = decide, {}

    def __call__(self, message, conversation, turn):
        first = self.first.setdefault(conversation, message)
        return self.decide(first, conversation, turn)


