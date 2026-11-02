from pathlib import Path

import pytest
import yaml

from perfrepair.dto.site import Edit, read_replacements
from perfrepair.files import read_json, write_json
from perfrepair.repair.__main__ import main
from perfrepair.repair.dependencies import dependencies, load
from perfrepair.run_dir import AppPaths
from perfrepair.source import language
from perfrepair.validation.repair import validate_edits, validate_harness
from repair_fixture import APP, JAVA, KOTLIN, ROOT, digests, pins, provider, replace, scope
from helpers import with_results

MANIFEST = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"
CURRENT, FAST = "Cipher|AES/GCM/NoPadding|Slow", "Cipher|AES/GCM/NoPadding|Fast"

LITERAL = scope(JAVA, "byte[] literal(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding", "Slow")', inputSize=1024, keySize=256)
NESTED = scope(JAVA, "byte[] nested(byte[] in)", 'Cipher.getInstance(name(prefix("AES"), "GCM"), "Slow")')
TWICE = scope(JAVA, "byte[] twice(byte[] in)", 'Cipher.getInstance("AES/GCM/NoPadding")')
TEMPLATE = scope(KOTLIN, "fun template(", 'Cipher.getInstance("AES/$mode/NoPadding", "Slow")')
SCOPES = [LITERAL, NESTED, TWICE, TEMPLATE]


def setup_run(tmp_path):
    paths = AppPaths(tmp_path, APP)
    paths.root.mkdir(parents=True)
    with_results(tmp_path)
    write_json(paths.facts, {"root": str(ROOT.resolve())})
    write_json(paths.scopes, {"schemaVersion": 1, "app": APP, "scopes": [s.to_json() for s in SCOPES]})
    write_json(paths.replacements, {"schemaVersion": 2, "app": APP, "replacements": [
        replace(LITERAL, provider("Fast"), option=FAST).to_json(), replace(NESTED, provider("Fast"), option=FAST).to_json(),
        replace(TWICE, pins(tagBits=128), option=FAST).to_json(), replace(TEMPLATE, provider("Fast"), option=FAST).to_json()]})
    write_json(paths.dossiers, {"dossiers": [{"scope": {"id": s.id}, "current": CURRENT} for s in SCOPES]})
    return paths


def commands(tmp_path):
    paths = setup_run(tmp_path)
    assert main(["edit", "--device-results", str(tmp_path), "--app", str(ROOT)]) == 0
    assert main(["harness", "--device-results", str(tmp_path), "--app", str(ROOT)]) == 0
    return paths


def test_edit_then_harness_lists_each_applied_scope_with_both_functions(tmp_path):
    before = digests()
    paths = commands(tmp_path)
    assert digests() == before
    edits = read_json(paths.edits)
    assert validate_edits(edits, APP, {s.id for s in SCOPES}) == []
    doc = yaml.safe_load(paths.harness.read_text())
    assert validate_harness(doc, APP, paths.root, edits) == []
    assert [s["id"] for s in doc["scopes"]] == sorted([LITERAL.id, NESTED.id, TEMPLATE.id])
    entry = next(s for s in doc["scopes"] if s["id"] == LITERAL.id)
    assert entry == {
        "id": LITERAL.id, "language": "java", "function": "byte[] literal(byte[] in)",
        "before": f"harness/{LITERAL.id}/before.java", "after": f"harness/{LITERAL.id}/after.java",
        "imports": ["import java.security.Security;", "import javax.crypto.Cipher;", "import javax.crypto.SecretKey;",
                    "import javax.crypto.spec.GCMParameterSpec;"],
        "inputs": {"inputSize": 1024, "keySize": 256, "from": "app"}, "current": CURRENT, "option": FAST,
        "metrics": ["timeNs", "allocationCount", "energyJ"], "dependencies": ["key"]}
    original = (ROOT / JAVA).read_text().splitlines(keepends=True)
    assert (paths.root / entry["before"]).read_text() == "".join(original[LITERAL.start - 1:LITERAL.end])
    assert '"Fast"' in (paths.root / entry["after"]).read_text()
    kotlin = next(s for s in doc["scopes"] if s["id"] == TEMPLATE.id)
    assert (kotlin["language"], kotlin["option"], kotlin["dependencies"]) == ("kotlin", FAST, ["secret"])
    nested = next(s for s in doc["scopes"] if s["id"] == NESTED.id)
    assert nested["dependencies"] == ["key", "name", "prefix"]
    assert nested["inputs"] == {"inputSize": 1024, "keySize": 128, "from": "run"}


def test_both_steps_are_deterministic(tmp_path):
    first, second = commands(tmp_path / "a"), commands(tmp_path / "b")
    assert first.edits.read_bytes() == second.edits.read_bytes()
    assert first.harness.read_bytes() == second.harness.read_bytes()
    assert digests(first.root) == digests(second.root)


def test_dependencies_skip_locals_parameters_lambdas_and_imports():
    java = "byte[] f(byte[] in) {\n  int n = in.length;\n  for (byte b : in) { n += b; }\n  return this.key.x(n, helper(in), (a, c) -> a);\n}\n"
    assert dependencies(java, language.JAVA, ["import a.b.Helper;"], load("java")) == ["helper", "key"]
    kotlin = "fun g(x: Int): Int {\n  val y = x + offset\n  return listOf(y).map { it + 1 }.sum()\n}\n"
    assert dependencies(kotlin, language.KOTLIN, [], load("kotlin")) == ["offset"]


def test_validators_refuse_broken_documents(tmp_path):
    paths = commands(tmp_path)
    edits = read_json(paths.edits)
    bad = {**edits, "edits": edits["edits"] + [{"scope": "x", "status": "rejected", "reason": "guess", "diff": ""}]}
    assert len(validate_edits(bad, APP, {s.id for s in SCOPES})) == 2
    doc = yaml.safe_load(paths.harness.read_text())
    doc["scopes"][0]["metrics"] = ["timeNs"]
    doc["scopes"] = doc["scopes"][:2]
    problems = validate_harness(doc, APP, paths.root, edits)
    assert any("applied edits" in p for p in problems) and any("metrics" in p for p in problems)
    doc["scopes"][1]["current"] = doc["scopes"][1]["option"]
    assert any("are not two items" in p for p in validate_harness(doc, APP, paths.root, edits))


def test_an_unknown_edit_kind_is_rejected(tmp_path):
    paths = setup_run(tmp_path)
    write_json(paths.replacements, {"schemaVersion": 2, "app": APP, "replacements": [
        replace(LITERAL, Edit("rename_class")).to_json()]})
    assert main(["edit", "--device-results", str(tmp_path), "--app", str(ROOT)]) == 0
    assert read_json(paths.edits)["edits"][0]["reason"] == "unsupported_kind"


def test_a_replacements_file_of_another_version_is_refused():
    with pytest.raises(ValueError, match="replacements schemaVersion 1 is not 2"):
        read_replacements({"schemaVersion": 1, "app": APP, "replacements": []})
