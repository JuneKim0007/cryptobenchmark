import re

import pytest
import yaml
from grouping_data import BENCHMARK, FAMILIES, INVENTORY, NAMES, PREPARED, PROBE, TRIAL

from perfrepair.dto.grouping import items_document, profiles_document
from perfrepair.files import write_json
from perfrepair.grouping.build.items import build
from perfrepair.ai.parse.grouping_assign.kind import charter
from perfrepair.run_dir import GroupingPaths

from helpers import LIBRARY, QUIET  # noqa: F401  (re-exported for grouping tests)

CHARTER = charter(LIBRARY)


@pytest.fixture
def paths(tmp_path):
    items, profiles = build(PROBE, NAMES, TRIAL, FAMILIES, INVENTORY, PREPARED, BENCHMARK)
    p = GroupingPaths(tmp_path)
    p.root.mkdir()
    write_json(p.items, items_document(items))
    write_json(p.profiles, profiles_document(profiles))
    return p


def item_name(task):
    return yaml.safe_load(task.text)["item"]["name"]


def by_name(task, *_):
    name, message = item_name(task), yaml.safe_load(task.text)
    for group in message["groups"]:
        if any(m.startswith(f"{name} @") for m in group["members"]):
            return {"group": group["id"], "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "same"}
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return {"group": "", "newGroup": {"id": slug, "description": f"the function {name}"}, "amend": [], "reason": "new"}
