"""Each AI role against its row of catalog/role-contracts.yaml: inputs, prompt and tools, files written, output, faults."""
import hashlib
import json
import shutil
from dataclasses import replace
from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml
from helpers import LIBRARY
from role_runs import ROLES, assigned_device, built_device

from perfrepair.ai.evaluate.worthiness.kind import charter as worthiness_charter
from perfrepair.ai.parse.algorithm_classify.kind import charter as classify_charter
from perfrepair.ai.parse.grouping_assign.kind import charter as assign_charter
from perfrepair.ai.repair.upgrade.kind import charter as upgrade_charter
from perfrepair.ai.runtime.agent import ScriptedConversations
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.ai.runtime.engine.tracking import MissingInput, role_run, stamp
from perfrepair.ai.suggest.site_replace.kind import charter as replace_charter
from perfrepair.catalog import role_contracts as contracts
from perfrepair.catalog.role_contracts import ContractError, role_contracts
from perfrepair.check.contracts import charter_problems, check_contracts
from perfrepair.dto.charter import read_charter
from perfrepair.files import read_json
from perfrepair.stop import code_of

BY_NAME = {r.name: r for r in ROLES}
GOLDEN = Path(__file__).parent / "fixtures" / "role_renders"
CHARTERS = {"screening.classify": classify_charter(LIBRARY, ""), "grouping.assign": assign_charter(LIBRARY),
            "worthiness": worthiness_charter(LIBRARY),
            "apps.replace": replace_charter(LIBRARY), "repair-upgrade": upgrade_charter(LIBRARY),
            "review.stability": replace_charter(LIBRARY)}
ROLE = pytest.mark.parametrize("role", ROLES, ids=lambda r: r.name)


@pytest.fixture(autouse=True)
def every_item_asked(asked_by_model):
    yield


@pytest.fixture
def built(tmp_path):
    return built_device(tmp_path / "built")


@pytest.fixture
def assigned(built, tmp_path):
    return assigned_device(built, tmp_path / "assigned")


@pytest.fixture
def base(built, assigned):
    return {"built": built, "assigned": assigned}


def device_for(role, base, tmp_path):
    device = tmp_path / "device"
    shutil.copytree(base[role.base], device)
    return device


def contract(role):
    return role_contracts()[role.name].bind(**role.names)


def asked(role, device, answer=None):
    conversations = ScriptedConversations(answer or role.right)
    role.run(device, conversations)
    return conversations


def journal(role, device):
    return [json.loads(line) for line in (device / contract(role).folder / "journal.jsonl").read_text().splitlines()]


def snapshot(device):
    return {str(p.relative_to(device)): hashlib.sha256(p.read_bytes()).hexdigest() for p in device.rglob("*") if p.is_file()}


# the row


def test_every_role_has_one_row_with_no_tools():
    rows = role_contracts()
    assert set(rows) == {r.name for r in ROLES} == set(CHARTERS)
    assert all(row.tools == () for row in rows.values())


@pytest.mark.parametrize("name", CHARTERS)
def test_a_row_pins_the_charter_its_role_builds(name):
    assert charter_problems(role_contracts()[name], CHARTERS[name]) == []
    assert role_contracts()[name].prompt in LIBRARY.entries


@pytest.mark.parametrize("edit, problem", [
    (lambda r: r.pop("tools"), "contracts_invalid"),
    (lambda r: r.update(stray=1), "contracts_invalid"),
    (lambda r: r.update(charter="short"), "12 hex digits"),
    (lambda r: r.update(optional=r["required"]), "both required and optional"),
    (lambda r: r.update(required=[]), "no required input"),
])
def test_the_loader_refuses_a_broken_row(tmp_path, edit, problem):
    doc = yaml.safe_load(contracts.CATALOG.read_text())
    edit(doc["roles"]["worthiness"])
    path = tmp_path / "rows.yaml"
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(ContractError, match=problem):
        contracts.load(path)


# inputs


@ROLE
def test_each_call_records_every_input_with_its_digest_and_the_replay_accepts_it(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    lines = journal(role, device)
    assert lines and all(line["role"] == role.name for line in lines)
    for line in lines:
        files = {i["file"]: i["digest"] for i in line["inputs"]}
        assert contract(role).required_missing(list(files)) == []
        run_files = {f: d for f, d in files.items() if (device / f).is_file() and not f.startswith("catalog/")}
        assert run_files and all(hashlib.sha256((device / f).read_bytes()).hexdigest() == d for f, d in run_files.items())
    assert all(not found for found in check_contracts(device).values())


def rewrite_lines(role, device, change):
    path = device / contract(role).folder / "journal.jsonl"
    path.write_text("".join(json.dumps(change(json.loads(line))) + "\n" for line in path.read_text().splitlines()))


def problems_of(role, device):
    return check_contracts(device)[f"{contract(role).folder} contract {role.name}"]


@ROLE
def test_the_replay_fails_a_required_input_that_never_reached_the_call(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    required = contract(role).required[0]
    rewrite_lines(role, device, lambda line: {**line, "inputs": [i for i in line["inputs"] if not fnmatchcase(i["file"], required)]})
    assert any(f"required input {required}" in p for p in problems_of(role, device))


@ROLE
def test_the_replay_fails_an_input_outside_the_contract(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    rewrite_lines(role, device, lambda line: {**line, "inputs": [*line["inputs"], {"file": "secret.json", "digest": "0"}]})
    assert any("secret.json is outside the contract" in p for p in problems_of(role, device))


@ROLE
def test_the_replay_fails_a_call_with_no_record(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    rewrite_lines(role, device, lambda line: {k: v for k, v in line.items() if k not in ("role", "inputs")})
    assert any("no recorded inputs" in p for p in problems_of(role, device))


def test_an_unreadable_journal_is_a_problem_not_a_crash(base, tmp_path):
    role = BY_NAME["repair-upgrade"]
    device = device_for(role, base, tmp_path)
    asked(role, device)
    (device / contract(role).folder / "journal.jsonl").write_text("not json\n")
    assert any("journal_unreadable" in p for p in problems_of(role, device))


def test_the_reader_hears_a_read_no_loader_declared(built):
    with role_run("repair-upgrade", built, app="app"):
        # a plain read in no loader: the file event is what is heard
        Path(built / "rows.json").read_text()
        heard = {i["file"] for i in stamp()["inputs"]}
    assert "rows.json" in heard and not role_contracts()["repair-upgrade"].bind(app="app").declares("rows.json")


def test_outside_a_role_run_nothing_is_stamped(built):
    Path(built / "rows.json").read_text()
    assert stamp() == {}


# prompt and tools


def active_charter(role, device):
    outbox = active_outbox(device / contract(role).folder)
    return outbox.directory / "charter.json"


@ROLE
@pytest.mark.parametrize("edit, problem", [
    (lambda c: replace(c, tools=("write_catalog",)), "tools"),
    (lambda c: replace(c, schema={"type": "object"}), "schema differs"),
    (lambda c: replace(c, system=replace(c.system, name="other/prompt")), "prompt other/prompt"),
    (lambda c: replace(c, system=replace(c.system, text="edited")), "charter hash"),
])
def test_a_charter_off_its_row_fails(role, edit, problem):
    assert any(problem in p for p in charter_problems(role_contracts()[role.name], edit(CHARTERS[role.name])))


def test_the_replay_reads_the_charter_of_the_active_outbox(base, tmp_path):
    role = BY_NAME["repair-upgrade"]
    device = device_for(role, base, tmp_path)
    asked(role, device)
    path = active_charter(role, device)
    doc = read_json(path)
    assert charter_problems(contract(role), read_charter(doc)) == []
    path.write_text(json.dumps({**doc, "tools": ["write_catalog"]}))
    assert any("tools ['write_catalog']" in p for p in problems_of(role, device))


def test_a_prompt_a_person_overrode_is_held_to_its_name_and_schema_not_the_pin():
    charter = CHARTERS["worthiness"]
    source = ((charter.system.name, "/mine/worthiness.system.md"),)
    assert charter_problems(role_contracts()["worthiness"], replace(charter, system=replace(charter.system, text="mine"), sources=source)) == []


# writes


@ROLE
def test_a_run_changes_only_what_the_row_says_and_the_record_agrees(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    before = snapshot(device)
    asked(role, device)
    after = snapshot(device)
    changed = {f for f in {*before, *after} if before.get(f) != after.get(f)}
    row = contract(role)
    assert changed and [f for f in changed if not row.may_write(f)] == []
    assert set(row.writes) <= changed and any(row.bookkeeping(f) for f in changed)
    recorded = set(read_json(device / row.folder / "writes.json")["files"])
    assert {f for f in changed if not f.startswith("log/")} - recorded <= {f"{row.folder}/writes.json", "grouping/classify/batches.json"}


@ROLE
def test_the_replay_fails_a_file_written_outside_the_row(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    path = device / contract(role).folder / "writes.json"
    doc = read_json(path)
    path.write_text(json.dumps({**doc, "files": [*doc["files"], "catalog/groups.yaml"]}))
    assert any("wrote catalog/groups.yaml" in p for p in problems_of(role, device))


# output


@ROLE
def test_the_outbox_rebuilds_each_file_byte_for_byte(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    assert role.replay(device) == []
    for path in role.files(device):
        path.write_bytes(path.read_bytes() + b" ")
        assert any("byte for byte" in p for p in role.replay(device)), path
        path.write_bytes(path.read_bytes()[:-1])
    assert role.replay(device) == []


@ROLE
def test_the_golden_render(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    conversations = asked(role, device)
    message = conversations.turns[0][2]
    assert message.text + "\n" == (GOLDEN / f"{role.name}.txt").read_text()


def test_stability_sends_what_replace_sends(base, tmp_path):
    role_a, role_b = BY_NAME["apps.replace"], BY_NAME["review.stability"]
    a = asked(role_a, device_for(role_a, base, tmp_path))
    shutil.rmtree(tmp_path / "device")
    b = asked(role_b, device_for(role_b, base, tmp_path))
    assert a.turns[0][2].text == b.turns[0][2].text


@ROLE
def test_an_identical_rerun_makes_no_call(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device)
    assert asked(role, device).started == 0


# gate C and faults


def dropped(role, device):
    records = active_outbox(device / contract(role).folder).records()
    assert records and all(r.outcome == "dropped" and r.decision is None for r in records)
    errors = (device / contract(role).folder / "errors.jsonl").read_text().splitlines()
    assert len(errors) == len(records)
    return records


@ROLE
def test_an_answer_citing_an_id_not_in_its_message_is_refused(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    asked(role, device, role.wrong_id)
    assert all(role.cited in " ".join(r.problems) for r in dropped(role, device))


@pytest.mark.parametrize("role", [r for r in ROLES if r.name != "screening.classify"], ids=lambda r: r.name)
def test_a_missing_required_input_is_one_code_before_any_call(role, base, tmp_path):
    device = device_for(role, base, tmp_path)
    for path in device.glob(next(p for p in contract(role).required if not p.startswith("catalog/"))):
        path.unlink()
    conversations = ScriptedConversations(role.right)
    with pytest.raises(MissingInput) as e:
        role.run(device, conversations)
    assert code_of(e.value) == "missing_input" and conversations.started == 0


def test_classify_writes_its_one_input_itself_and_refuses_when_it_is_gone(built):
    with pytest.raises(MissingInput):
        with role_run("screening.classify", built):
            pass
