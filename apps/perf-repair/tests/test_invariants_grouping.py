import copy
import shutil
from pathlib import Path

import pytest
from perfrepair.files import write_json
from perfrepair.validation.finding import ADVISORY, BLOCKING, UNDECIDED
from perfrepair.validation.grouping import invariants as inv
from perfrepair.validation.invariants import load_grouping, run_invariants
from perfrepair.validation.invariants.__main__ import main

EMU = Path(__file__).parent / "fixtures" / "invariants" / "emu-api30"
DIGEST = "code_d3c08f376c"


@pytest.fixture
def g():
    return load_grouping(EMU)


def group(g, gid):
    return next(x for x in g.groups["groups"] if x["id"] == gid)


def subjects(found, invariant):
    return sorted(v.subject for v in found if v.invariant == invariant)


def test_the_emulator_run_fails_both_mixed_generator_groups_and_the_all_unknown_one(g):
    found = inv.key_contract_agrees(g, {})
    # aes-keygen-exportable: every member unknown too; #98's key contracts are what make it pass
    assert subjects(found, "key_contract_agrees") == ["group aes-keygen", "group aes-keygen-exportable", "group rsa-keypair-gen"]
    assert all(v.severity == BLOCKING for v in found)
    assert "KeyGenerator|AES|AndroidKeyStore keyContract unknown, key component unknown" in group_evidence(found, "aes-keygen")


def group_evidence(found, gid):
    return next(v.evidence for v in found if v.subject == f"group {gid}")


def test_the_command_exits_1_on_the_emulator_run(capsys):
    assert main([str(EMU)]) == 1
    assert "blocking key_contract_agrees group aes-keygen:" in capsys.readouterr().out


def test_mixed_contracts_are_reported_from_report_s_own_finding(g):
    g.checks.append({"kind": "key_contract_differs", "group": DIGEST, "detail": "members hold both", "items": []})
    assert "group code_d3c08f376c" in subjects(inv.key_contract_agrees(g, {}), "key_contract_agrees")


def test_a_component_two_members_know_differently_breaks_the_signature(g):
    assert inv.signature_agrees(g) == []
    member = str(group(g, DIGEST)["members"][0])
    comps = g.profiles[member]["signature"]["components"]
    next(c for c in comps if c["name"] == "function")["value"] = "OTHER"
    found = inv.signature_agrees(g)
    assert subjects(found, "signature_agrees") == ["group code_d3c08f376c"]
    assert any(e.startswith("function=OTHER") for e in found[0].evidence)


def test_resolved_parameters_differ_blocks(g):
    g.checks.append({"kind": "resolved_parameters_differ", "group": DIGEST, "detail": "SHA-1 | SHA-256", "items": []})
    assert subjects(inv.signature_agrees(g), "signature_agrees") == ["group code_d3c08f376c"]


def test_an_option_from_a_group_with_no_runnable_member_blocks(g):
    dossiers = {"app": {"dossiers": [{"scope": {"id": "s1"}, "current": "KeyGenerator|AES|AndroidOpenSSL",
                                      "options": [{"alias": "R1", "item": "KeyGenerator|AES|BC"}]}]}}
    found = inv.no_runnable_no_options(g, dossiers)
    assert [v.subject for v in found] == ["app scope s1"] and "group aes-keygen has no runnable member" in found[0].evidence
    dossiers["app"]["dossiers"][0]["options"][0]["item"] = "KeyGenerator|AES|BundledConscrypt"
    assert inv.no_runnable_no_options(g, dossiers) == []


def test_interop_not_run_is_advisory_and_silent_once_checked(g):
    found = inv.interop_not_run(g)
    assert {v.severity for v in found} == {ADVISORY} and "group aes-keygen-exportable" in subjects(found, "interop_not_run")
    g.groups["interop"] = {"status": "checked", "pairs": []}
    assert inv.interop_not_run(g) == []


def split(g):
    x = group(g, DIGEST)
    moved = x["members"].pop()
    g.groups["groups"].append({**x, "id": "digest-split", "members": [moved], "runnable": []})
    g.groups["items"][str(moved)]["group"] = "digest-split"
    return g


def test_one_name_in_two_groups_with_equal_facts_is_an_advisory_split(g):
    assert inv.algorithm_split(g) == []
    found = inv.algorithm_split(split(g))
    assert [(v.subject, v.severity) for v in found] == [("digest.none SHA-256", ADVISORY)]


def test_the_same_input_in_two_runs_gives_the_same_groups(g):
    other = load_grouping(EMU)
    assert inv.grouping_stable(g, other) == []
    found = inv.grouping_stable(g, split(copy.deepcopy(other)))
    assert len(found) == 2 and {v.severity for v in found} == {BLOCKING}


def test_an_input_that_changed_is_not_compared(g):
    other = split(copy.deepcopy(load_grouping(EMU)))
    moved = str(group(other, "digest-split")["members"][0])
    other.profiles[moved]["runs"] = not other.profiles[moved]["runs"]
    assert inv.grouping_stable(g, other) == []


def test_an_absent_input_is_undecided_never_a_silent_pass(tmp_path):
    app = tmp_path / "bare" / "demo"
    app.mkdir(parents=True)
    write_json(app / "app.json", {"root": str(tmp_path), "projectRoot": "."})
    found = run_invariants(tmp_path / "bare")
    assert {(v.invariant, v.severity) for v in found} == {("inputs_present", UNDECIDED)}
    assert sorted(Path(v.evidence[0]).name for v in found) == ["checks.json", "groups.json", "profiles.json", "scopes.json"]
    shutil.copytree(EMU, tmp_path / "d")
    (tmp_path / "d" / "grouping" / "checks.json").unlink()
    assert [Path(v.evidence[0]).name for v in run_invariants(tmp_path / "d") if v.severity == UNDECIDED] == ["checks.json"]


def test_run_invariants_reads_a_device_folder_with_no_apps(tmp_path):
    shutil.copytree(EMU, tmp_path / "d")
    assert {v.invariant for v in run_invariants(tmp_path / "d")} == {"key_contract_agrees", "interop_not_run"}


def screened_out(g, gid):
    for m in group(g, gid)["members"]:
        g.groups["items"][str(m)]["screen"] = "broken"


def offering(g, gid):
    item = g.groups["items"][str(group(g, gid)["members"][0])]["qualified"]
    return {"app": {"dossiers": [{"scope": {"id": "s1"}, "current": "x", "options": [{"alias": "R1", "item": item}]}]}}


def test_a_group_every_member_screened_out_and_offered_nowhere_is_exempt_from_the_key_contract(g):
    screened_out(g, "aes-keygen")
    g.checks.append({"kind": "key_contract_differs", "group": "aes-keygen", "detail": "members hold both", "items": []})
    assert "group aes-keygen" not in subjects(inv.grouping_invariants(g, {}), "key_contract_agrees")


def test_a_screened_out_group_a_dossier_offers_still_answers_to_the_key_contract(g):
    screened_out(g, "aes-keygen")
    assert "group aes-keygen" in subjects(inv.key_contract_agrees(g, offering(g, "aes-keygen")), "key_contract_agrees")


def test_one_member_not_screened_out_keeps_the_group_under_the_key_contract(g):
    g.groups["items"][str(group(g, "aes-keygen")["members"][0])]["screen"] = "broken"
    g.groups["items"][str(group(g, "aes-keygen")["members"][1])]["screen"] = "accepted"
    assert "group aes-keygen" in subjects(inv.key_contract_agrees(g, {}), "key_contract_agrees")
