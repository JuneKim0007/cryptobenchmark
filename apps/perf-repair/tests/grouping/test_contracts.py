import json
import re
from dataclasses import replace

import pytest
from perfrepair.dto.signature import Component, Signature
import yaml
from conftest import CHARTER, LIBRARY, QUIET, by_name
from grouping_data import FAMILIES

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind
from perfrepair.ai.parse.grouping_assign.render import render
from perfrepair.ai.review.grouping_review.render import render as review_render
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN, Item, Profile, profiles_document, read_profiles
from perfrepair.dto.grouping_state import Group, Knowledge
from perfrepair.dto.interop import member, pair_status
from perfrepair.files import read_json, write_json
from perfrepair.grouping.interop_plan import write_plan
from perfrepair.grouping.interop_read import import_results
from perfrepair.grouping.report.checks import report
from perfrepair.grouping.report.rules import check
from perfrepair.validation.grouping.interop import validate_interop, validate_plan
from perfrepair.validation.grouping.items import validate_items

ITEMS = {1: Item(1, "TypeC", "S/M", "P1", "cipher.secret"), 2: Item(2, "TypeC", "S/M", "P2", "cipher.secret"),
         3: Item(3, "TypeC", "S/N", "P3", "cipher.secret")}


def profile(contract):
    return Profile("secret", "measured", True, True, keyContract=contract)


def kinds(contracts):
    profiles = {n: profile(c) for n, c in contracts.items()}
    knowledge = Knowledge(1, {"g": Group("cipher.secret", "g", list(contracts))}, [])
    return [f for f in check(knowledge, ITEMS, profiles) if f.kind == "key_contract_differs"]


def test_a_group_holding_both_known_contracts_is_an_error():
    finding, = kinds({1: KEY_APP_HELD, 2: KEY_PROVIDER_HELD})
    assert (finding.severity, finding.group, finding.items) == ("error", "g", (1, 2))


@pytest.mark.parametrize("contracts", [{1: KEY_APP_HELD, 2: KEY_APP_HELD}, {1: KEY_PROVIDER_HELD, 2: KEY_PROVIDER_HELD},
                                       {1: KEY_APP_HELD, 2: KEY_UNKNOWN}, {1: KEY_PROVIDER_HELD, 2: KEY_UNKNOWN}])
def test_unknown_or_one_contract_is_no_finding(contracts):
    assert kinds(contracts) == []


def rendered(item_contract, member_contract):
    keyed = lambda c: replace(profile(c), signature=None if c == KEY_UNKNOWN else Signature((Component("key", c),)))
    profiles = {1: keyed(member_contract), 3: keyed(item_contract)}
    knowledge = Knowledge(1, {"g": Group("cipher.secret", "g", [1])}, [])
    return render(ITEMS[3], FAMILIES.by_id["cipher.secret"], knowledge, ITEMS, profiles)


def test_assign_shows_the_key_line_for_the_item_and_the_group():
    text = rendered(KEY_PROVIDER_HELD, KEY_APP_HELD)
    assert text.index("key: application-held") < text.index("\nitem:") < text.index("key: inside the provider")


def test_assign_shows_no_key_line_for_unknown():
    assert "key:" not in rendered(KEY_UNKNOWN, KEY_UNKNOWN)


def test_review_shows_the_key_of_known_members():
    items = {"1": {"qualified": "TypeC|S/M|P1", "keyContract": KEY_APP_HELD},
             "2": {"qualified": "TypeC|S/M|P2", "keyContract": KEY_UNKNOWN}}
    text = review_render("f", "d", [{"id": "g", "description": "g", "members": [1, 2]}], items, [])
    assert "1 · S/M · P1 · key: application-held" in text
    assert re.search(r"^  2 · S/M · P2$", text, re.M)


def test_a_contract_outside_the_set_is_refused():
    assert any("key contract" in p for p in validate_items(
        [ITEMS[1]], {1: Profile("secret", "measured", True, True, keyContract="elsewhere")}, FAMILIES))


def test_profiles_of_the_old_schema_are_refused():
    with pytest.raises(ValueError, match="rerun grouping build"):
        read_profiles({"schemaVersion": 1, "profiles": {}})


@pytest.mark.parametrize("name", ["parse/grouping-assign", "review/grouping-review"])
def test_the_prompts_are_directives_with_the_three_contracts(name):
    text = LIBRARY.system(name, id_pattern="P", max_description=9).text if name.startswith("parse") else LIBRARY.system(name).text
    assert not re.search(r"\b(because|so that|costs?|since|in order to|why)\b", text, re.I)
    assert all(c in text for c in ("input contract", "key contract", "output contract", "application-held", "inside the provider"))
    assert "key store" not in text
    assert "provider identity" in text


@pytest.fixture
def across(paths):
    """A finished grouping whose first group of two runnable members crosses key contracts."""
    decide(GroupingKind(paths, FAMILIES), CHARTER, ScriptedConversations(by_name), paths.root, **QUIET)
    group = next(g for g in report(paths, FAMILIES)["groups"] if len(g["runnable"]) > 1)
    a, b = group["runnable"][:2]
    profiles = read_profiles(read_json(paths.profiles))
    profiles[a], profiles[b] = replace(profiles[a], keyContract=KEY_APP_HELD), replace(profiles[b], keyContract=KEY_PROVIDER_HELD)
    write_json(paths.profiles, profiles_document(profiles))
    return paths, group["id"], report(paths, FAMILIES)["items"], a, b


def test_a_pair_across_key_contracts_is_never_planned_and_reads_not_checkable(across, tmp_path):
    paths, gid, items, a, b = across
    qa, qb = items[str(a)]["qualified"], items[str(b)]["qualified"]
    planned = write_plan(paths)
    assert frozenset((qa, qb)) not in {frozenset((p.a, p.b)) for p in planned}
    written = yaml.safe_load(paths.interop_plan.read_text())
    assert [r["id"] for r in written["notCheckable"]] == [len(planned) + 1]
    assert pair_status(report(paths, FAMILIES), qa, qb) == "not_run"

    rows = [{"id": p.id, "group": p.group, "a": member(p.a), "b": member(p.b), "result": "pass",
             "directions": {"aToB": "pass", "bToA": "pass"}, "reason": ""} for p in planned]
    source = tmp_path / "interop.yaml"
    source.write_text(yaml.safe_dump({"schemaVersion": 1, "pairs": rows}))
    import_results(paths, source)
    groups = report(paths, FAMILIES)
    assert pair_status(groups, qa, qb) == "not_checkable"
    findings = json.loads(paths.checks.read_text())["findings"]
    assert {f["kind"] for f in findings if f["group"] == gid} >= {"key_contract_differs", "interop_not_checkable"}
    assert all(v == [] for v in validate_interop(groups, paths.interop_plan, paths.interop).values())


def test_a_plan_pairing_across_key_contracts_is_refused(across):
    paths, gid, items, a, b = across
    groups = report(paths, FAMILIES)
    pair = {"id": 1, "group": gid, "a": member(items[str(a)]["qualified"]), "b": member(items[str(b)]["qualified"])}
    assert any("across key contracts" in p for p in validate_plan({"schemaVersion": 1, "pairs": [pair]}, groups))
