"""A generator's key contract from the key its trial produced, the cross-check with the provider's consumers, and the rule
that an unknown generator joins no group; the providers are made up."""
import pytest
from perfrepair.catalog.families import Families
from perfrepair.catalog.names import Names
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN
from perfrepair.dto.grouping_state import Answer, Group, Knowledge, code_made
from perfrepair.dto.screen import Verdict
from perfrepair.grouping.build.items import build
from perfrepair.grouping.build.key_contract import cross_checked, generator_contract
from perfrepair.grouping.report.rules import check
from perfrepair.screen.groups import code_groups, identified
from perfrepair.validation.grouping.invariants import Grouping, key_contract_agrees
from perfrepair.validation.parse.grouping_assign import validate_answer

FAMILIES = Families.load()
RAW = {"works": True, "keySize": 128, "keyMaterial": "exportable", "keyFormat": "RAW"}
HELD = {"works": True, "keySize": 128, "keyMaterial": "non_exportable"}


@pytest.mark.parametrize("engine,runs,want", [
    ("KeyGenerator", [RAW], KEY_APP_HELD),
    ("KeyPairGenerator", [{**RAW, "keyFormat": "PKCS#8"}], KEY_APP_HELD),
    ("KeyGenerator", [HELD], KEY_PROVIDER_HELD),
    ("KeyGenerator", [{**HELD, "keyFormat": "RAW"}], KEY_PROVIDER_HELD),
    ("KeyGenerator", [{**RAW, "keyFormat": "PKCS#8"}], KEY_UNKNOWN),
    ("KeyPairGenerator", [RAW], KEY_UNKNOWN),
    ("KeyGenerator", [{**RAW, "keyFormat": None}], KEY_UNKNOWN),
    ("KeyGenerator", [{"works": True, "keySize": 128}], KEY_UNKNOWN),
    ("KeyGenerator", [{"works": False, "error": "IllegalStateException: Not initialized"}], KEY_UNKNOWN),
    ("KeyGenerator", [], KEY_UNKNOWN),
    ("KeyGenerator", [RAW, HELD], KEY_UNKNOWN),
])
def test_the_produced_key_decides_and_doubt_is_unknown(engine, runs, want):
    assert generator_contract(engine, runs) == want


def test_consumers_that_disagree_make_it_unknown_with_a_reason():
    assert cross_checked(KEY_APP_HELD, {KEY_APP_HELD, KEY_UNKNOWN}) == (KEY_APP_HELD, None)
    contract, conflict = cross_checked(KEY_APP_HELD, {KEY_PROVIDER_HELD})
    assert contract == KEY_UNKNOWN and conflict.startswith("key_contract_conflict")
    assert cross_checked(KEY_UNKNOWN, {KEY_PROVIDER_HELD}) == (KEY_UNKNOWN, None)


def _built(runs: dict, consumer_classes: dict | None = None, consumer_run: dict | None = None):
    consumer_classes = consumer_classes or {}
    services = []
    for p, run in runs.items():
        services.append({"provider": p, "type": "KeyGenerator", "algorithm": "AES", "instantiates": True, "defaultRun": run})
        services.append({"provider": p, "type": "Cipher", "algorithm": "AES/GCM/NoPadding", "instantiates": True,
                         "defaultRun": consumer_run or {"works": True, "keyAlgorithm": "AES", "keyProvider": p, "inputSize": 1024}})
    probe = Probe({"providers": [{"name": p, "services": [
        {"type": "KeyGenerator", "algorithm": "AES"},
        {"type": "Cipher", "algorithm": "AES/GCM/NoPadding",
         "attributes": {"SupportedKeyClasses": consumer_classes[p]} if p in consumer_classes else {}}]} for p in runs]})
    items, profiles = build(probe, probe.names(Names.load()), {"services": services}, FAMILIES)
    return {i.provider: i for i in items if i.type == "KeyGenerator"}, items, profiles


def test_build_takes_the_contract_from_the_trial_and_flags_a_conflict():
    gens, _, profiles = _built({"A": RAW, "B": HELD, "C": RAW, "D": {"works": False, "error": "x"}}, {"C": "vendor.Handle"})
    contract = {p: profiles[i.id].keyContract for p, i in gens.items()}
    assert contract == {"A": KEY_APP_HELD, "B": KEY_PROVIDER_HELD, "C": KEY_UNKNOWN, "D": KEY_UNKNOWN}
    assert profiles[gens["C"].id].keyContractConflict.startswith("key_contract_conflict")
    findings = check(Knowledge(), {i.id: i for i in gens.values()}, profiles)
    assert [(f.kind, f.items) for f in findings if f.kind == "key_contract_conflict"] == [("key_contract_conflict", (gens["C"].id,))]


def test_a_consumer_that_refused_the_generated_key_still_cross_checks_it():
    failed = {"works": False, "error": "InvalidKeyException: not one of its handles"}
    gens, _, profiles = _built({"C": RAW}, {"C": "vendor.Handle"}, failed)
    assert profiles[gens["C"].id].keyContract == KEY_UNKNOWN
    assert profiles[gens["C"].id].keyContractConflict.startswith("key_contract_conflict")


def test_a_size_whose_key_disagrees_makes_the_built_generator_unknown_and_a_refused_size_says_nothing():
    sized = {**RAW, "triedKeys": [{"size": 256, "keyMaterial": "non_exportable"}]}
    other_format = {**RAW, "triedKeys": [{"size": 256, "keyMaterial": "exportable", "keyFormat": "PKCS#8"}]}
    refused = {**RAW, "triedKeys": [{"size": 192, "refused": True}, {"size": 256, "keyMaterial": "exportable", "keyFormat": "RAW"}]}
    gens, _, profiles = _built({"A": sized, "B": other_format, "C": refused})
    assert {p: profiles[i.id].keyContract for p, i in gens.items()} == {"A": KEY_UNKNOWN, "B": KEY_UNKNOWN, "C": KEY_APP_HELD}
    assert profiles[gens["A"].id].isolated and not profiles[gens["C"].id].isolated


def test_an_unknown_generator_is_a_code_made_group_of_its_own():
    gens, items, profiles = _built({"A": RAW, "B": RAW, "D": {"works": False, "error": "x"}, "E": {"works": False, "error": "x"}})
    verdicts = {i.id: Verdict("unknown", "r", canonical="AES") for i in items}
    groups = code_groups(items, verdicts, profiles)
    group_of = {m: gid for gid, g in groups.items() for m in g.members}
    assert group_of[gens["A"].id] == group_of[gens["B"].id]
    assert groups[group_of[gens["D"].id]].members == [gens["D"].id] != groups[group_of[gens["E"].id]].members
    assert code_made(group_of[gens["D"].id]) and code_made(group_of[gens["E"].id]) and not code_made(group_of[gens["A"].id])
    assert identified(gens["D"], verdicts, profiles)


def test_gate_c_refuses_an_unknown_generator_in_any_model_group():
    gens, _, profiles = _built({"A": RAW, "D": {"works": False, "error": "x"}})
    a, d = gens["A"], gens["D"]
    knowledge = Knowledge(groups={"aes-keygen": Group(a.family, "AES generators", [a.id])})
    join = Answer("aes-keygen", "", "", (), "same function")
    assert any("joins no group" in p for p in validate_answer(join, d, knowledge, FAMILIES, profiles))
    knowledge = Knowledge(groups={"aes-keygen": Group(d.family, "AES generators", [d.id])})
    assert any("joins no group" in p for p in validate_answer(join, a, knowledge, FAMILIES, profiles))


def _invariant(items, profiles, groups):
    entries = {str(i.id): {"qualified": i.qualified, "keyContract": profiles[i.id].keyContract, "screen": "accepted"} for i in items}
    document = {"items": entries, "groups": [{"id": gid, "members": g.members} for gid, g in groups.items()]}
    return key_contract_agrees(Grouping(document, {str(k): p.to_json() for k, p in profiles.items()}, [], {}), {})


def test_key_contract_agrees_passes_the_code_made_generator_groups_and_refuses_an_unknown_one_in_a_group():
    gens, items, profiles = _built({"A": RAW, "B": RAW, "C": HELD, "D": HELD, "E": {"works": False, "error": "x"}})
    verdicts = {i.id: Verdict("unknown", "r", canonical="AES") for i in items}
    groups = {gid: g for gid, g in code_groups(items, verdicts, profiles).items() if g.family == gens["A"].family}
    assert sorted(len(g.members) for g in groups.values()) == [1, 2, 2]
    assert _invariant(items, profiles, groups) == []
    forced = {"wrong": Group(gens["A"].family, "d", [gens["A"].id, gens["E"].id])}
    assert [v.subject for v in _invariant(items, profiles, forced)] == ["group wrong"]
