"""Who is asked: a listed name never, an unlisted one once; catalog groups by key contract; candidates; gate C on the facts."""
import json
from pathlib import Path

import pytest
import yaml
from conftest import LIBRARY, QUIET
from helpers import CATALOG as SCREEN_CATALOG

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.kind import project
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.catalog import groups as catalog_file
from perfrepair.catalog.algorithms import Algorithms, algorithms
from perfrepair.catalog.families import Families
from perfrepair.catalog.names import fold
from perfrepair.catalog.groups import (
    CATALOG,
    GroupsError,
    _describe,
    _row_id,
    group_catalog,
    load,
    row_contracts,
)
from perfrepair.catalog.interchange import interchange
from perfrepair.catalog.names import Names
from perfrepair.catalog.screening import Screening
from perfrepair.catalog.signature import signature
from perfrepair.catalog.types import types
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.device.coverage import coverage
from perfrepair.dto.grouping import KEY_PROVIDER_HELD, items_document, profiles_document
from perfrepair.dto.grouping_state import Group, code_made
from perfrepair.dto.screen import screen_document
from perfrepair.dto.signature import UNKNOWN
from perfrepair.files import read_document, write_json
from perfrepair.grouping.build.items import build
from perfrepair.grouping.report.checks import report
from perfrepair.grouping.report.rules import check
from perfrepair.run_dir import GroupingPaths, built
from perfrepair.screen.handler import ScreeningHandler
from perfrepair.validation.parse.grouping_assign import SLUG

NAMES, FAMILIES = Names.load(), Families.load()
SCREENING = Screening.load(names=NAMES)
RAW, HANDLE = {"SupportedKeyFormats": ["RAW"]}, {"SupportedKeyClasses": ["vendor.store.HandleSecretKey"]}
OAEP = "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"
HMAC, GCM = "HmacSHA256", "AES/GCM/NoPadding"
DIGEST = "MD5"
RESOLVED = {("P1", OAEP): "digest=SHA-256 mgf1=SHA-1", ("P2", OAEP): "digest=SHA-256 mgf1=SHA-256"}


def service(engine_type, name, attributes=None):
    return {"type": engine_type, "algorithm": name, "attributes": attributes or {}}


PROBE = Probe({"providers": [
    {"name": "P1", "services": [service("Mac", HMAC, RAW), service("Cipher", OAEP, RAW), service("MessageDigest", DIGEST),
                                service("Cipher", GCM, RAW)]},
    {"name": "P2", "services": [service("Mac", "HMACSHA256", RAW), service("Cipher", OAEP, RAW), service("Cipher", GCM, HANDLE)]},
]})
TRIAL = {"services": [{"provider": p["name"], "type": s["type"], "algorithm": s["algorithm"], "instantiates": True,
                       "defaultRun": {"works": True, "providerChose": RESOLVED.get((p["name"], s["algorithm"]))}}
                      for p in PROBE._document["providers"] for s in p["services"]]}


@pytest.fixture
def paths(tmp_path):
    paths = GroupingPaths(tmp_path)
    paths.root.mkdir()
    names = PROBE.names(NAMES)
    items, profiles = build(PROBE, names, TRIAL, FAMILIES)
    write_json(paths.items, items_document(items))
    write_json(paths.profiles, profiles_document(profiles))
    handler = ScreeningHandler(SCREENING, names)
    write_json(paths.screen, screen_document({i.id: handler.verdict(i.type, i.name) for i in items},
                                             SCREEN_CATALOG, built(paths)))
    return paths


def new_group(task, *_):
    item = yaml.safe_load(task.text)["item"]
    return {"group": "", "newGroup": {"id": f"model-{item['id']}", "description": "d"}, "amend": [], "reason": "r"}


def run(paths, answers=new_group):
    kind = GroupingKind(paths, FAMILIES)
    agent = ScriptedConversations(answers)
    return decide(kind, charter(LIBRARY, kind.inputs), agent, paths.root, **QUIET), agent, kind


def item(kind, qualified):
    return next(i for i in kind.items() if i.qualified == qualified)


def test_a_listed_name_is_never_asked_and_an_unlisted_one_is_one_fresh_call_of_system_knowledge_item(paths):
    knowledge, agent, kind = run(paths)
    asked = sorted(i.qualified for i in kind.pending())
    assert asked == [f"Cipher|{OAEP}|P1", f"Cipher|{OAEP}|P2"]
    assert agent.started == len(asked) == 2 and len(active_outbox(paths.root).records()) == 2
    assert [turn for _, turn, _ in agent.turns] == [1, 1]
    assert all("interchangeability group" in s.text for s in agent.systems)
    first, second = (yaml.safe_load(m.text) for _, _, m in agent.turns)
    assert {"family", "groups", "item"} == set(first) == set(second)
    # group knowledge is built per call: the second call sees the group the first answer made
    assert f"model-{first['item']['id']}" in {g["id"] for g in second["groups"]}
    assert f"model-{first['item']['id']}" not in {g["id"] for g in first["groups"]}


def test_a_screened_out_item_is_never_asked_and_stays_in_its_code_group(paths):
    knowledge, agent, kind = run(paths)
    md5 = item(kind, f"MessageDigest|{DIGEST}|P1")
    assert md5 not in kind.pending() and code_made(knowledge.group_of(md5.id))
    assert all(yaml.safe_load(m.text)["item"]["name"] != DIGEST for _, _, m in agent.turns)


def test_a_catalog_group_spans_spellings_and_providers_and_splits_by_key_contract(paths):
    knowledge, _, kind = run(paths)
    mac = {knowledge.group_of(item(kind, q).id) for q in (f"Mac|{HMAC}|P1", "Mac|HMACSHA256|P2")}
    assert mac == {"mac-s-hmacsha256"}
    held, app = item(kind, f"Cipher|{GCM}|P2"), item(kind, f"Cipher|{GCM}|P1")
    assert kind.profiles[held.id].keyContract == KEY_PROVIDER_HELD
    assert knowledge.group_of(app.id) == "cipher-s-aes-gcm-nopadding"
    assert knowledge.group_of(held.id) == "cipher-s-aes-gcm-nopadding.p"
    assert "inside the provider" in knowledge.groups["cipher-s-aes-gcm-nopadding.p"].description


def test_two_oaep_providers_with_different_mgf1_are_not_merged_by_name(paths):
    kind = GroupingKind(paths, FAMILIES)
    p1, p2 = item(kind, f"Cipher|{OAEP}|P1"), item(kind, f"Cipher|{OAEP}|P2")
    assert {p1, p2} <= set(kind.pending())
    assert group_catalog().of(p1.family, OAEP) is None
    knowledge = kind.empty()
    knowledge.groups["oaep"] = Group(p1.family, "d", [p1.id])
    join = '{"group": "oaep", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    _, problems = kind.check(p2, join, knowledge)
    assert any("mgf1=SHA-1" in p and "mgf1=SHA-256" in p for p in problems)


def test_a_listed_name_whose_trial_resolved_what_its_row_does_not_state_goes_to_the_model(paths):
    document = read_document(paths.items)
    row = next(r for r in document["items"] if r["name"] == GCM and r["provider"] == "P1")
    row["resolved"] = "digest=SHA-256 mgf1=SHA-1"
    write_json(paths.items, document)
    write_json(paths.screen, {**read_document(paths.screen), "built": built(paths)})
    kind = GroupingKind(paths, FAMILIES)
    assert item(kind, f"Cipher|{GCM}|P1") in kind.pending()


def test_a_call_chosen_resolved_parameter_keeps_a_listed_name_listed(paths):
    document = read_document(paths.items)
    row = next(r for r in document["items"] if r["name"] == GCM and r["provider"] == "P1")
    row["resolved"] = "GCM iv=12B tagBits=128"
    write_json(paths.items, document)
    write_json(paths.screen, {**read_document(paths.screen), "built": built(paths)})
    kind = GroupingKind(paths, FAMILIES)
    assert item(kind, f"Cipher|{GCM}|P1") not in kind.pending()


def test_candidates_carry_provenance_and_nothing_is_promoted(paths):
    before = CATALOG.read_bytes()
    run(paths)
    report(paths, FAMILIES)
    document = yaml.safe_load(paths.group_candidates.read_text())
    (family, rows), = document["families"].items()
    assert sorted(r["provenance"]["decisions"][0]["item"] for r in rows) == [f"Cipher|{OAEP}|P1", f"Cipher|{OAEP}|P2"]
    assert {r["contracts"]["output"]["mgf1"] for r in rows} == {"SHA-1", "SHA-256"}
    for row in rows:
        decision = row["provenance"]["decisions"][0]
        assert row["provenance"]["source"] == "model" and {"model", "run", "date", "seq"} <= set(decision)
        assert "findings" in row["provenance"]["checks"]
    assert CATALOG.read_bytes() == before
    group_catalog.cache_clear()
    assert group_catalog().of(family, OAEP) is None


def test_a_rebuild_keeps_each_decision_s_run_and_date(paths):
    run(paths)
    report(paths, FAMILIES)
    document = yaml.safe_load(paths.group_candidates.read_text())
    for row in next(iter(document["families"].values())):
        row["provenance"]["decisions"][0].update(run="earlier", date="2026-01-01")
        row["description"] = "edited"
    paths.group_candidates.write_text(yaml.safe_dump(document))
    report(paths, FAMILIES)
    again = next(iter(yaml.safe_load(paths.group_candidates.read_text())["families"].values()))
    assert {(r["provenance"]["decisions"][0]["run"], r["provenance"]["decisions"][0]["date"]) for r in again} == {("earlier", "2026-01-01")}
    assert {r["description"] for r in again} == {"d"}


def test_a_resumed_run_asks_nothing_new_and_coverage_counts_the_asked(paths):
    run(paths)
    assert coverage(paths).asked == 2 and coverage(paths).pending == ()
    _, agent, _ = run(paths)
    assert agent.started == 0


def test_a_model_may_join_a_catalog_group_but_never_amend_it_or_cross_its_key_contract(paths):
    kind = GroupingKind(paths, FAMILIES)
    knowledge = kind.empty()
    oaep = item(kind, f"Cipher|{OAEP}|P1")
    knowledge.groups["cipher-p-rsa-ecb-pkcs1padding"] = Group(oaep.family, "d", [])
    join = '{"group": "cipher-p-rsa-ecb-pkcs1padding", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    assert kind.check(oaep, join, knowledge)[1] == []
    amend = ('{"group": "", "newGroup": {"id": "own", "description": "d"}, "reason": "r", '
             '"amend": [{"group": "cipher-p-rsa-ecb-pkcs1padding", "description": "x"}]}')
    assert any("description is fixed" in p for p in kind.check(oaep, amend, knowledge)[1])
    mac = item(kind, f"Mac|{HMAC}|P1")
    other = kind.check(mac, join, knowledge)[1]
    assert any("is not a group of family mac.secret" in p and f"family {oaep.family}" in p for p in other)


def test_a_join_contradicting_a_known_key_contract_is_refused_naming_it_and_a_consistent_one_passes(paths):
    kind = GroupingKind(paths, FAMILIES)
    knowledge = kind.empty()
    held = item(kind, f"Cipher|{GCM}|P2")
    join = '{"group": "cipher-s-aes-gcm-nopadding", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    _, problems = kind.check(held, join, knowledge)
    assert any("key=app_held" in p and "key=provider_held" in p for p in problems)
    knowledge.groups["mine"] = Group(held.family, "d", [held.id])
    consistent = '{"group": "mine", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    assert not [p for p in kind.check(held, consistent, knowledge)[1] if "key=" in p]


def test_a_model_group_the_signature_would_split_and_a_catalog_group_that_disagrees_are_findings(paths):
    run(paths)
    kind = GroupingKind(paths, FAMILIES)
    knowledge = project(kind, active_outbox(paths.root).records())
    p1, p2 = item(kind, f"Cipher|{OAEP}|P1"), item(kind, f"Cipher|{OAEP}|P2")
    knowledge.groups["together"] = Group(p1.family, "d", [p1.id, p2.id])
    knowledge.groups["cipher-p-rsa-ecb-pkcs1padding"] = Group(p1.family, "d", [p1.id, p2.id])
    found = {f.kind: f for f in check(knowledge, kind.by_id, kind.profiles)}
    assert "mgf1" in found["signature_would_split"].detail and found["signature_would_split"].group == "together"
    assert found["catalog_signature_differs"].group == "cipher-p-rsa-ecb-pkcs1padding"


def test_report_on_catalog_and_model_groups_validates(paths):
    run(paths)
    document = report(paths, FAMILIES)
    assert {"mac-s-hmacsha256", "model-" + str(next(i for i in GroupingKind(paths, FAMILIES).pending()).id)} <= {g["id"] for g in document["groups"]}


def test_the_committed_catalog_loads_and_each_row_agrees_with_the_signature():
    catalog = load()
    assert len(catalog.groups) > 100 and catalog.source
    for group in catalog.groups:
        engine_type = FAMILIES.by_id[group.family].type
        assert SLUG.match(group.id + ".p") and len(group.description) <= 400
        # the signature reads only the names its regex rules know; every other name's facts are its catalogue entry
        ruled = [n for _, n in group.members if interchange().engines[engine_type].rule_of(n) and fold(f"{engine_type}|{n}") in MASTER_MEMBERS]
        read = {signature(engine_type, name, None, "app_held", NAMES).identity for name in ruled}
        assert len(read) <= 1 and not any(c[1] is None for i in read for c in i)


@pytest.mark.parametrize("group, code", [
    ({"algorithms": ["Mac|HmacSHA256"], "exemplars": [], "description": "d"}, "unknown"),
    ({}, "missing"),
    ({"exemplars": [], "algorithms": ["HmacSHA256"]}, "no Mac|<canonical> id"),
    ({"exemplars": [], "algorithms": ["Cipher|HmacSHA256"]}, "no Mac|<canonical> id"),
    ({"exemplars": [], "algorithms": ["Mac|HMAC-SHA256"]}, "no canonical"),
    ({"exemplars": [], "algorithms": ["Mac|AES"]}, "no canonical"),
    ({"exemplars": [], "algorithms": ["Mac|HmacSHA256", "Mac|HMACSHA256"]}, "no canonical|listed twice"),
    ({"exemplars": ["Mac|HmacMD5"], "algorithms": ["Mac|HmacSHA256"]}, "exemplar .* is no member"),
])
def test_a_bad_group_is_refused(tmp_path, group, code):
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 3, "source": "t", "groups": {"mac.secret": group}}))
    with pytest.raises(GroupsError, match=code):
        load(path)


def test_a_member_without_a_catalogue_entry_is_refused(tmp_path):
    entries = algorithms()
    catalogue = Algorithms(tuple(e for e in entries.entries if e.id != "Mac|HmacSHA256"), entries.common)
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 3, "source": "t", "groups": {"mac.secret": {"exemplars": [], "algorithms": ["Mac|HmacSHA256"]}}}))
    with pytest.raises(GroupsError, match="no entry in mac.secret's catalogue"):
        load(path, catalogue=catalogue)


def test_a_stray_family_and_an_old_schema_are_refused(tmp_path):
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 3, "source": "t", "groups": {"nope": {"algorithms": []}}}))
    with pytest.raises(GroupsError, match="not a family"):
        load(path)
    path.write_text(yaml.safe_dump({"schemaVersion": 2, "source": "t", "groups": {}}))
    with pytest.raises(GroupsError, match="groups_schema"):
        load(path)
    assert catalog_file.CATALOG == CATALOG


def test_the_catalog_is_one_group_per_family_and_lists_every_typed_name():
    catalog = group_catalog()
    assert {g.family for g in catalog.families} == {f.id for f in FAMILIES.all}
    for group in catalog.families:
        typed = {name for (family, name) in types().rows if family == group.family}
        assert typed <= {n.upper() for n in group.algorithms}


MASTER_ROWS = json.loads((Path(__file__).parents[1] / "fixtures" / "contract-rows-master.json").read_text())
MASTER_MEMBERS = {fold(m) for r in MASTER_ROWS for m in r["members"]}
# each row that gained a member at this catalogue review, and why the member's contract equals the row's
# a master member now a spelling of another id: one registration under two names
MERGED = {"Mac|PBEWITHHMACSHA": "Mac|PBEWithHmacSHA1"}
JOINED = json.loads((Path(__file__).parents[1] / "fixtures" / "contract-rows-joined.json").read_text())


def _folded(values: dict) -> dict:
    """One spelling per value changed only case and separators, and curve became parameterSet where the value is a parameter set."""
    plain = {k: fold(str(v)).replace(" ", "").replace("-", "") for k, v in values.items()}
    if plain.get("scheme") in ("MLDSA", "SLHDSA") and "curve" in plain:
        plain["parameterSet"] = plain.pop("curve")
    return plain


def _key_of(group) -> str:
    return "none" if group.keyless else "password" if group.password else "app"


def test_every_master_row_stands_with_only_its_listed_differences():
    """Rows compare spelled by fold; cipher.unknown's rows are cipher.secret's, a password row's key is `password`, a listed joiner joins."""
    catalog, found = group_catalog(), []
    at = {fold(f"{t}|{n}"): g for g in catalog.groups for t, n in g.members}
    at.update({fold(alias): at[fold(target)] for alias, target in MERGED.items()})
    for row in MASTER_ROWS:
        family = "cipher.secret" if row["family"] == "cipher.unknown" else row["family"]
        assert [m for m in row["members"] if fold(m) not in at] == [], row["id"]
        groups = {at[fold(m)].id for m in row["members"]}
        assert len(groups) == 1, row["id"]
        g = at[fold(row["members"][0])]
        assert g.family == family
        password = row["input"].get("passwordBased") == "TRUE"
        assert g.password == password
        assert _key_of(g) == ("password" if password else row["key"]), row["id"]
        assert (_folded(g.contracts["input"]), _folded(g.contracts["output"])) == (_folded(row["input"]), _folded(row["output"])), row["id"]
        added = sorted(f"{t}|{n}" for t, n in g.members if fold(f"{t}|{n}") not in {fold(m) for m in row["members"]})
        found += [(row["id"], added)] * bool(added)
    assert {k: v["members"] for k, v in JOINED.items()} == dict(found)
    assert all(v["why"] for v in JOINED.values())


def test_the_row_count_is_what_the_review_measured():
    # 221 at master, plus one row per contract the reviewed names add
    assert (len(group_catalog().groups), len(MASTER_ROWS)) == (923, 221)


def test_a_password_row_has_no_provider_held_variant_and_says_password():
    row = group_catalog().of("cipher.secret", "PBEWithHmacSHA1AndAES_128")
    assert row.password and group_catalog().variant_of(row.id + ".p") is None
    assert "password" in group_catalog().variant_of(row.id).description


def test_an_assumed_value_is_a_row_s_value_and_its_description_says_assumed():
    row = group_catalog().of("mac.secret", "PBEWithHmacSHA256")
    assert row.contracts["input"]["kdf"] == "PBEWithHmac provider convention"
    assert "kdf=PBEWithHmac provider convention (assumed)" in row.description


def test_a_row_is_keyless_by_its_contract_key_as_the_engine_s_interchange_key_was():
    keyless = {g.family: g.keyless for g in group_catalog().groups}
    assert keyless == {f: interchange().engines[FAMILIES.by_id[f].type].key == "none" for f in keyless}
    assert {f for f, k in keyless.items() if k} == {"digest.none"}


def test_a_group_member_only_shares_a_row_when_its_contracts_are_equal():
    catalog = group_catalog()
    assert catalog.of("digest.none", "MD5") is not catalog.of("digest.none", "SHA-256")
    assert catalog.of("cipher.secret", "AES/CBC/PKCS5Padding") is not catalog.of("cipher.secret", "AES/GCM/NoPadding")


def test_a_listed_name_with_an_open_contract_has_no_row_so_the_model_decides():
    catalog = group_catalog()
    assert "RSA/ECB/OAEPPadding" in next(g for g in catalog.families if g.family == "cipher.pair").algorithms
    assert catalog.of("cipher.pair", "RSA/ECB/OAEPPadding") is None


@pytest.mark.parametrize("held, code", [
    ({"exemplars": [], "algorithms": [], "reason": "r"}, "fields"),
    ({"algorithms": []}, "fields"),
    ({"exemplars": ["Mac|X"], "algorithms": ["Mac|X"]}, "exemplars is not empty"),
    ({"exemplars": [], "algorithms": "Mac|X"}, "not a list"),
    ({"exemplars": [], "algorithms": ["X"]}, "no <type>|<name> id"),
    ({"exemplars": [], "algorithms": ["Mac|X", "MAC|x"]}, "listed twice"),
])
def test_a_bad_unidentified_group_is_refused_at_load(tmp_path, held, code):
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 3, "source": "t", "groups": {"unidentified": held}}))
    with pytest.raises(GroupsError, match=code):
        load(path)
