import copy
import re

import pytest

from perfrepair.ai.evaluate.worthiness.schema import SCHEMA as WORTHINESS
from perfrepair.ai.parse.algorithm_classify.schema import SCHEMA as CLASSIFY
from perfrepair.ai.parse.grouping_assign.schema import SCHEMA as ASSIGN
from perfrepair.ai.review.grouping_review.schema import SCHEMA as REVIEW
from perfrepair.ai.runtime.gateway.claude_api import API_UNSUPPORTED, api_schema
from perfrepair.ai.suggest.site_replace.schema import SCHEMA as REPLACE
from perfrepair.dto.site import OPTION_PREFIX
from perfrepair.validation.answer_text import NOT_BLANK
from perfrepair.validation.evaluate.worthiness import MEMBER_PREFIX
from perfrepair.validation.parse.grouping_assign import MAX_DESCRIPTION, SLUG

# What the role schemas may send the Messages API; a new keyword is checked against the API before it joins this.
API_KEYWORDS = {"type", "properties", "required", "additionalProperties", "items", "enum"}
SCHEMAS = {"assign": ASSIGN, "worthiness": WORTHINESS, "review": REVIEW, "replace": REPLACE, "classify": CLASSIFY}


def nodes(node):
    yield node
    for child in node.get("properties", {}).values():
        yield from nodes(child)
    if isinstance(node.get("items"), dict):
        yield from nodes(node["items"])


def matches(node, text):
    return re.search(node["pattern"], text) is not None


@pytest.mark.parametrize("name", SCHEMAS)
def test_every_field_required_no_nullable_and_patterns_compile(name):
    for node in nodes(SCHEMAS[name]):
        assert isinstance(node["type"], str)
        if node["type"] == "object":
            assert set(node["required"]) == set(node["properties"]) and node["additionalProperties"] is False
        if "pattern" in node:
            re.compile(node["pattern"])


@pytest.mark.parametrize("name", SCHEMAS)
def test_every_reason_is_not_blank(name):
    reasons = [n["properties"]["reason"] for n in nodes(SCHEMAS[name]) if "reason" in n.get("properties", {})]
    assert reasons and all(r["pattern"] == NOT_BLANK for r in reasons)
    assert not matches(reasons[0], " \n") and matches(reasons[0], "x")


def test_assign_limits_come_from_the_gate():
    new, amend = ASSIGN["properties"]["newGroup"]["properties"], ASSIGN["properties"]["amend"]["items"]["properties"]
    assert new["description"]["maxLength"] == amend["description"]["maxLength"] == MAX_DESCRIPTION
    for node in (ASSIGN["properties"]["group"], new["id"]):
        assert SLUG.pattern in node["pattern"]
        assert matches(node, "") and matches(node, "aes-gcm") and not matches(node, '""')
        assert not matches(node, "code_0123456789") and not matches(node, "Bad Id")
    assert amend["group"]["pattern"] == SLUG.pattern and not matches(amend["group"], "")


def test_alias_patterns_follow_the_minted_prefixes():
    member = WORTHINESS["properties"]["pairs"]["items"]["properties"]["from"]
    assert all(matches(member, f"{MEMBER_PREFIX}{n}") for n in (1, 9, 12))
    assert not any(matches(member, a) for a in (f"{MEMBER_PREFIX}0", "", "1", f"{MEMBER_PREFIX}1 "))
    option = REPLACE["properties"]["members"]["items"]["properties"]["option"]
    assert matches(option, f"{OPTION_PREFIX}3") and not matches(option, "") and not matches(option, f"{OPTION_PREFIX}0")


@pytest.mark.parametrize("name", SCHEMAS)
def test_the_api_schema_drops_what_the_messages_api_refuses_and_keeps_the_rest(name):
    schema = SCHEMAS[name]
    before = copy.deepcopy(schema)
    sent = api_schema(schema)
    assert schema == before
    assert not any(k in n for n in nodes(sent) for k in API_UNSUPPORTED)
    assert [n.get("enum") for n in nodes(sent)] == [n.get("enum") for n in nodes(schema)]
    assert [sorted(n.get("properties", {})) for n in nodes(sent)] == [sorted(n.get("properties", {})) for n in nodes(schema)]


@pytest.mark.parametrize("name", SCHEMAS)
def test_a_role_schema_sends_only_allowed_keywords(name):
    for node in nodes(api_schema(SCHEMAS[name])):
        assert set(node) <= API_KEYWORDS, sorted(set(node) - API_KEYWORDS)


def test_a_property_named_like_a_keyword_survives():
    sent = api_schema({"type": "object", "properties": {"pattern": {"type": "string", "pattern": "x"}},
                       "required": ["pattern"], "additionalProperties": False})
    assert sent["properties"] == {"pattern": {"type": "string"}}


def test_a_classify_reason_may_not_be_blank():
    reason = CLASSIFY["properties"]["answers"]["items"]["properties"]["reason"]
    assert reason["pattern"] == NOT_BLANK and not matches(reason, "  ") and matches(reason, "RFC 6151")
