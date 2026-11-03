from pathlib import Path

import pytest
import yaml
from conftest import LIBRARY, QUIET
from helpers import CATALOG as SCREEN_CATALOG

from perfrepair.ai.parse.grouping_assign.kind import GroupingKind, charter
from perfrepair.ai.parse.grouping_assign.render import render
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.catalog.families import Families
from perfrepair.catalog.interchange import CATALOG as INTERCHANGE, interchange, load
from perfrepair.catalog.names import CATALOG, Names
from perfrepair.catalog.screening import Screening
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.device.coverage import coverage
from perfrepair.dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN, Item, Profile, items_document, profiles_document
from perfrepair.dto.grouping_state import Group, code_made
from perfrepair.dto.screen import Verdict, screen_document
from perfrepair.dto.signature import CONVENTION, EXPORTABLE, KEY_MATERIAL, NON_EXPORTABLE, UNKNOWN
from perfrepair.files import read_document, write_json
from perfrepair.grouping.build.items import build
from perfrepair.grouping.report.checks import report
from perfrepair.grouping.signature import signature
from perfrepair.run_dir import GroupingPaths, built
from perfrepair.screen.groups import code_group_id, code_groups, grouped_by_code, screened_out, signature_group_id
from perfrepair.screen.handler import ScreeningHandler
from perfrepair.validation.parse.grouping_assign import _signature_problems
from perfrepair.validation.grouping.output import validate_output
from perfrepair.validation.parse.grouping_assign import MAX_DESCRIPTION

NAMES, FAMILIES = Names.load(), Families.load()
SCREENING = Screening.load(names=NAMES)
RUNTIMES = Path(__file__).parents[1] / "fixtures" / "runtimes"
RAW = {"SupportedKeyFormats": ["RAW"]}
HANDLE = {"SupportedKeyClasses": ["vendor.store.HandleKey"]}

# pending items asked, before and after the signature; a catalog or interchange change that moves these is deliberate
ASKED = {"jdk17": (155, 28), "jdk21": (162, 28), "jdk25": (176, 36), "android36": (119, 23)}


def sig(engine_type, name, resolved=None, contract=KEY_APP_HELD):
    return signature(engine_type, name, resolved, contract, NAMES)


def status(s, component):
    return next(c.status for c in s.components if c.name == component)


def test_key_size_iv_and_tag_do_not_split_and_mode_and_padding_do():
    one = sig("Cipher", "AES_128/GCM/NoPadding", "ivBytes=12 tagBits=128")
    assert one == sig("Cipher", "AES/GCM/NoPadding", "GCM iv=12B") == sig("Cipher", "aes_256/gcm/nopadding")
    assert one.decided and one.known()["mode"] == "GCM"
    assert one.differing(sig("Cipher", "AES/CBC/NoPadding")) == ["mode"]
    assert sig("Cipher", "AES/CBC/PKCS7Padding") == sig("Cipher", "AES/CBC/PKCS5Padding")


def test_oaep_is_known_only_from_resolved_never_the_names_default():
    name_only = sig("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", contract=KEY_PROVIDER_HELD)
    assert not name_only.decided and status(name_only, "mgf1") == UNKNOWN and name_only.known()["digest"] == "SHA-256"
    bare = sig("Cipher", "RSA/ECB/OAEPPadding")
    assert status(bare, "digest") == status(bare, "mgf1") == UNKNOWN


def test_oaep_resolved_decides_across_spellings_and_splits_mgf1():
    same = sig("Cipher", "RSA/ECB/OAEPPadding", "digest=SHA-1 mgf1=SHA-1 labelBytes=0")
    assert same.decided and same == sig("Cipher", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding", "OAEP digest=SHA1 mgf1=SHA-1")
    apart = sig("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "digest=SHA-256 mgf1=SHA-1")
    assert apart.differing(sig("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding", "digest=SHA-256 mgf1=SHA-256")) == ["mgf1"]


def test_a_bare_name_has_no_mode_or_padding_it_could_default_to():
    bare = sig("Cipher", "AES")
    assert status(bare, "mode") == status(bare, "padding") == UNKNOWN and bare.known()["base"] == "AES"


@pytest.mark.parametrize("a, b, differs", [
    ("SHA256withECDSA", "SHA256withECDSAinP1363Format", "encoding"),
    ("NONEwithECDSA", "SHA256withECDSA", "digest"),
    ("Ed25519", "Ed448", "curve"),
    ("SHA256withRSA", "SHA256withRSA/PSS", "scheme"),
])
def test_signature_components_split(a, b, differs):
    assert differs in sig("Signature", a).differing(sig("Signature", b))


def test_password_based_splits_from_raw_and_pkcs12_from_the_other_kdf():
    assert "passwordBased" in sig("Mac", "PBEWithHmacSHA256").differing(sig("Mac", "HmacSHA256"))
    assert sig("Mac", "PBEWITHHMACSHA").identity == sig("Mac", "PBEWithHmacSHA1").identity
    assert sig("Mac", "HmacPBESHA256").identity != sig("Mac", "PBEWithHmacSHA256").identity


def test_a_derived_key_length_the_pbe_name_fixes_splits_but_a_call_key_size_does_not():
    assert sig("Cipher", "PBEWITHMD5AND128BITAES-CBC-OPENSSL") != sig("Cipher", "PBEWITHMD5AND256BITAES-CBC-OPENSSL")
    assert sig("Cipher", "PBEWithHmacSHA256AndAES_128") != sig("Cipher", "PBEWithHmacSHA256AndAES_256")
    assert sig("Cipher", "AES_128/GCM/NoPadding") == sig("Cipher", "AES_256/GCM/NoPadding")
    assert status(sig("Cipher", "PBEWithHmacSHA256AndAES_128"), "kdf") == CONVENTION


def test_a_missing_key_contract_is_assumed_where_the_comparison_supports_it_and_asked_for_generators():
    assumed = sig("Mac", "HmacSHA256", contract=KEY_UNKNOWN)
    assert assumed.decided and assumed.assumed == ("key",) and assumed.identity == sig("Mac", "HmacSHA256").identity
    assert not sig("KeyGenerator", "AES", contract=KEY_UNKNOWN).decided
    assert sig("KeyGenerator", "AES").decided and sig("KeyGenerator", "AES").assumed == ("consumer",)
    assert "key" not in {c.name for c in sig("MessageDigest", "SHA-256").components}


def test_key_material_comes_from_the_trial_else_the_key_contract_else_is_unknown():
    material = lambda s: next(c for c in s.components if c.name == KEY_MATERIAL)
    assert material(signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES, key_material=EXPORTABLE)).value == EXPORTABLE
    assert material(sig("KeyGenerator", "AES", contract=KEY_PROVIDER_HELD)).value == NON_EXPORTABLE
    assert material(sig("KeyGenerator", "AES")).value == EXPORTABLE
    assert material(sig("KeyGenerator", "AES", contract=KEY_UNKNOWN)).status == UNKNOWN
    assert KEY_MATERIAL not in {c.name for c in sig("Mac", "HmacSHA256").components}


def test_an_unrecorded_key_material_never_joins_a_recorded_one_and_two_unrecorded_may_join():
    made, unrecorded = (signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES, key_material=EXPORTABLE),
                        signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES))
    assert made.differing(unrecorded) == [KEY_MATERIAL] and unrecorded.differing(made) == [KEY_MATERIAL]
    assert unrecorded.differing(unrecorded) == []
    held = signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES, key_material=NON_EXPORTABLE)
    assert made.differing(held) == [KEY_MATERIAL]


def test_an_unknown_name_and_a_conflict_are_unknown():
    assert sig("Mac", "NOT-CATALOGUED").known() == {"key": KEY_APP_HELD} and not sig("Mac", "NOT-CATALOGUED").decided
    conflicted = Probe({"providers": [{"name": "P", "services": [{"type": "Mac", "algorithm": "HmacSHA256",
                                                                  "aliases": ["PBEWITHHMACSHA256"]}]}]}).names(NAMES)
    assert not signature("Mac", "PBEWITHHMACSHA256", None, KEY_APP_HELD, conflicted).decided


def test_every_catalogued_name_of_a_family_engine_has_a_rule():
    doc = yaml.safe_load(CATALOG.read_text())["names"]
    for engine_type in FAMILIES.types:
        for name in doc[engine_type]:
            assert interchange().engines[engine_type].rule_of(name), (engine_type, name)


def test_a_rule_naming_a_component_outside_its_splits_is_refused(tmp_path):
    doc = yaml.safe_load(INTERCHANGE.read_text())
    doc["engines"]["Mac"]["splits"].remove("kdf")
    path = tmp_path / "interchange.yaml"
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(ValueError, match="interchange_component"):
        load(path)


def runtime(name):
    probe = Probe(read_document(RUNTIMES / name / "probe.yaml"))
    names = probe.names(NAMES)
    items, profiles = build(probe, names, read_document(RUNTIMES / name / "trial.yaml"), FAMILIES)
    handler = ScreeningHandler(SCREENING, names)
    return items, profiles, {i.id: handler.verdict(i.type, i.name, i.provider) for i in items}


@pytest.mark.parametrize("name", sorted(ASKED))
def test_each_runtime_asks_what_its_signature_leaves_open(name):
    items, profiles, verdicts = runtime(name)
    before = [i for i in items if not screened_out(verdicts[i.id])]
    after = [i for i in items if not grouped_by_code(i.id, verdicts, profiles)]
    assert (len(before), len(after)) == ASKED[name]
    assert {i.family for i in after} <= {"keygen.none", "keypairgen.none", "signature.pair"}


@pytest.mark.parametrize("name", sorted(ASKED))
def test_each_runtimes_code_groups_place_each_coded_item_once_and_stay_within_a_description(name):
    items, profiles, verdicts = runtime(name)
    groups = code_groups(items, verdicts, profiles)
    placed = [m for g in groups.values() for m in g.members]
    assert sorted(placed) == [i.id for i in items if grouped_by_code(i.id, verdicts, profiles)]
    assert all(len(g.description) <= MAX_DESCRIPTION for g in groups.values())
    for g in groups.values():
        assert len({profiles[m].signature.identity for m in g.members if not screened_out(verdicts[m])}) <= 1


def service(engine_type, name, attributes=None):
    return {"type": engine_type, "algorithm": name, "attributes": attributes or {}}


PROBE = Probe({"providers": [
    {"name": "P1", "services": [service("Mac", "HmacSHA256", RAW), service("Cipher", "RSA/ECB/OAEPPadding", RAW),
                                service("KeyGenerator", "AES"), service("Signature", "SHA256withRSA/PSS", RAW)]},
    {"name": "P2", "services": [service("Mac", "HMACSHA256"), service("Cipher", "RSA/ECB/OAEPPadding", HANDLE),
                                service("KeyGenerator", "AES"), service("Signature", "SHA256withRSA/PSS", RAW)]},
    {"name": "P3", "services": [service("Mac", "HmacSHA256", HANDLE), service("Cipher", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding", RAW)]},
]})
RESOLVED = {("P1", "RSA/ECB/OAEPPadding"): "digest=SHA-1 mgf1=SHA-1", ("P3", "RSA/ECB/OAEPWithSHA-1AndMGF1Padding"): "digest=SHA-1 mgf1=SHA-1"}
TRIAL = {"services": [{"provider": p["name"], "type": s["type"], "algorithm": s["algorithm"], "instantiates": True,
                       "defaultRun": {"works": True, "providerChose": RESOLVED.get((p["name"], s["algorithm"]))}}
                      for p in PROBE._document["providers"] for s in p["services"]]}


@pytest.fixture
def chain(tmp_path):
    paths = GroupingPaths(tmp_path)
    paths.root.mkdir()
    names = PROBE.names(NAMES)
    items, profiles = build(PROBE, names, TRIAL, FAMILIES)
    write_json(paths.items, items_document(items))
    write_json(paths.profiles, profiles_document(profiles))
    handler = ScreeningHandler(SCREENING, names)
    write_json(paths.screen, screen_document({i.id: handler.verdict(i.type, i.name, i.provider) for i in items},
                                             SCREEN_CATALOG, built(paths)))
    return paths


def answer_new(task, *_):
    return {"group": "", "newGroup": {"id": f"g-{abs(hash(task.item)) % 10**8}", "description": "d"}, "amend": [], "reason": "r"}


def run(paths, answers=answer_new):
    kind = GroupingKind(paths, FAMILIES)
    agent = ScriptedConversations(answers)
    return decide(kind, charter(LIBRARY, kind.inputs), agent, paths.root, **QUIET), agent, kind


def members(knowledge, kind, gid_filter=code_made):
    return sorted(sorted(kind.by_id[m].qualified for m in g.members) for gid, g in knowledge.groups.items() if gid_filter(gid))


def test_a_decided_signature_is_grouped_by_code_and_only_the_rest_is_asked(chain):
    knowledge, agent, kind = run(chain)
    asked = sorted(i.qualified for i in kind.pending())
    assert asked == ["Cipher|RSA/ECB/OAEPPadding|P2", "KeyGenerator|AES|P1", "KeyGenerator|AES|P2"]
    assert agent.started == 3
    assert members(knowledge, kind) == [
        ["Cipher|RSA/ECB/OAEPPadding|P1", "Cipher|RSA/ECB/OAEPWithSHA-1AndMGF1Padding|P3"],
        ["Mac|HMACSHA256|P2", "Mac|HmacSHA256|P1"],
        ["Mac|HmacSHA256|P3"],
        ["Signature|SHA256withRSA/PSS|P1", "Signature|SHA256withRSA/PSS|P2"]]


def test_a_signature_group_id_is_a_digest_of_family_and_signature_not_of_the_run(chain):
    kind = GroupingKind(chain, FAMILIES)
    first = next(i for i in kind.items() if i.provider == "P1" and i.type == "Mac")
    other = next(i for i in kind.items() if i.provider == "P2" and i.type == "Mac")
    gid = signature_group_id(first, kind.profiles[first.id].signature)
    assert gid == signature_group_id(other, kind.profiles[other.id].signature) and code_made(gid)
    assert kind.empty().group_of(first.id) == gid


def test_coverage_counts_only_what_is_asked(chain):
    assert coverage(chain).asked == 3 and len(coverage(chain).pending) == 3
    run(chain)
    state = coverage(chain)
    assert state.asked == 3 and state.pending == ()


def test_report_accepts_signature_groups_and_marks_what_convention_assumed(chain):
    run(chain)
    document = report(chain, FAMILIES)
    kind = GroupingKind(chain, FAMILIES)
    assert validate_output(document, kind.by_id, kind.screen, kind.profiles) == []
    findings = [f for f in read_document(chain.checks)["findings"] if f["kind"] == "convention_assumed"]
    named = {kind.by_id[f["items"][0]].type: f for f in findings}
    assert set(named) == {"Mac", "Signature"} and all(f["severity"] == "warning" for f in findings)
    assert "key" in named["Mac"]["detail"] and "mgf1, salt" in named["Signature"]["detail"]


def test_validate_output_refuses_a_coded_item_in_a_model_group(chain):
    run(chain)
    document = report(chain, FAMILIES)
    kind = GroupingKind(chain, FAMILIES)
    coded = next(g for g in document["groups"] if code_made(g["id"]) and len(g["members"]) > 1)
    moved = coded["members"].pop()
    model = next(g for g in document["groups"] if not code_made(g["id"]))
    model["members"].append(moved)
    document["items"][str(moved)]["group"] = model["id"]
    problems = validate_output(document, kind.by_id, kind.screen, kind.profiles)
    assert any("its signature groups it by code" in p for p in problems)


def test_a_join_across_a_known_component_is_refused_and_an_unknown_one_decides_nothing(chain):
    kind = GroupingKind(chain, FAMILIES)
    knowledge = kind.empty()
    p1 = next(i for i in kind.items() if i.qualified == "Cipher|RSA/ECB/OAEPPadding|P2")
    target = next(i for i in kind.items() if i.qualified == "KeyGenerator|AES|P1")
    knowledge.groups["other"] = Group(p1.family, "d", [next(i.id for i in kind.items() if i.qualified == "Cipher|RSA/ECB/OAEPPadding|P1")])
    join = '{"group": "other", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    _, problems = kind.check(p1, join, knowledge)
    assert any("key=app_held" in p and "key=provider_held" in p for p in problems)
    knowledge.groups["gen"] = Group(target.family, "d", [next(i.id for i in kind.items() if i.qualified == "KeyGenerator|AES|P2")])
    join = '{"group": "gen", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": "r"}'
    assert kind.check(target, join, knowledge)[1] == []


def test_a_record_of_an_item_now_coded_adds_no_member_and_is_kept(chain):
    kind = GroupingKind(chain, FAMILIES)
    screened_profiles = read_document(chain.profiles)
    for row in screened_profiles["profiles"].values():
        row["signature"]["components"].append({"name": "name", "value": None, "status": "unknown"})
    write_json(chain.profiles, screened_profiles)
    write_json(chain.screen, {**read_document(chain.screen), "built": built(chain)})
    first, agent, kind = run(chain)
    assert agent.started == len(kind.items())
    records = len(active_outbox(chain.root).records())
    profiles = read_document(chain.profiles)
    for row in profiles["profiles"].values():
        row["signature"]["components"].pop()
    write_json(chain.profiles, profiles)
    write_json(chain.screen, {**read_document(chain.screen), "built": built(chain)})
    again, agent, kind = run(chain)
    assert agent.started == 0 and len(active_outbox(chain.root).records()) == records
    assert {m for g in again.groups.values() for m in g.members} == {i.id for i in kind.items()}
    assert sum(not code_made(g) for g in again.groups) == 3


def test_the_message_shows_the_signature_and_says_what_is_not_known(chain):
    kind = GroupingKind(chain, FAMILIES)
    item = next(i for i in kind.items() if i.qualified == "Cipher|RSA/ECB/OAEPPadding|P2")
    text = render(item, FAMILIES.by_id[item.family], kind.empty(), kind.by_id, kind.profiles)
    assert "signature: base=RSA, digest=not known, mgf1=not known, mode=ECB, padding=OAEP" in text
    assert "key: inside the provider" in text


def test_gate_c_splits_a_generator_that_ran_from_one_that_did_not_as_on_the_recorded_device():
    service = lambda provider, run: {"provider": provider, "type": "KeyGenerator", "algorithm": "AES", "instantiates": True, "defaultRun": run}
    trial = {"services": [service("P1", {"works": False, "error": "IllegalStateException: Not initialized"}),
                          service("P2", {"works": True, "keySize": 128, "keyMaterial": EXPORTABLE})]}
    probe = Probe({"providers": [{"name": p, "services": [{"type": "KeyGenerator", "algorithm": "AES"}]} for p in ("P1", "P2")]})
    items, profiles = build(probe, probe.names(NAMES), trial, FAMILIES)
    by_provider = {i.provider: i for i in items}
    assert profiles[by_provider["P2"].id].signature.known()[KEY_MATERIAL] == EXPORTABLE
    group = Group("f", "d", [by_provider["P2"].id])
    problems = _signature_problems("g", by_provider["P1"], {"g": group}, profiles)
    assert len(problems) == 1 and "keyMaterial=exportable" in problems[0] and "this item has keyMaterial=unknown" in problems[0]


def test_a_screened_out_generator_keeps_key_materials_apart_and_other_groups_keep_their_id():
    made, unrecorded = (signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES, key_material=EXPORTABLE),
                        signature("KeyGenerator", "AES", None, KEY_UNKNOWN, NAMES))
    item, verdict = Item(1, "KeyGenerator", "AES", "P1", "f"), Verdict("broken", "r", canonical="AES")
    ids = [code_group_id(item, verdict, Profile(signature=s, keyKind="none", keyKindFrom="x", instantiates=True, runs=True))
           for s in (made, unrecorded, made)]
    assert ids[0] == ids[2] != ids[1]
    mac = Profile(signature=sig("Mac", "HmacSHA256"), keyKind="none", keyKindFrom="x", instantiates=True, runs=True)
    assert code_group_id(item, verdict, mac) == code_group_id(item, verdict)
