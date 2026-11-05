import json

import pytest
from conftest import CHARTER, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.files import write_json
from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.ask import Limits
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.validation import ValidationFailed


def group(paths, agent, limits=Limits(), limit=None):
    return decide(GroupingKind(paths, FAMILIES), CHARTER, agent, paths.root, limits, limit, **QUIET)


def test_a_tampered_items_file_is_refused_at_pop(paths):
    doc = json.loads(paths.items.read_text())
    doc["items"][0]["group"] = "smuggled"
    write_json(paths.items, doc)
    with pytest.raises(ValidationFailed):
        group(paths, ScriptedConversations(by_name))
