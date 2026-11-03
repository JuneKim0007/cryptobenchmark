import re
from dataclasses import replace
from pathlib import Path

import pytest

from perfrepair.ai.suggest.site_replace.render import _lifecycle
from perfrepair.dto.lifecycle import Lifecycle, Requirement, Settled
from perfrepair.dto.site import Scope, required_risks, scope_id
from perfrepair.scope.engines import read_engines
from perfrepair.scope.facts import settled_key_source
from perfrepair.source.language import of_file
from perfrepair.validation.app import validate_scopes

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_java")
pytest.importorskip("tree_sitter_kotlin")

from perfrepair.scope.build import build_scopes  # noqa: E402
from perfrepair.scope.lifecycle.read import read_site  # noqa: E402
from perfrepair.scope.lifecycle.settle import settle  # noqa: E402
from perfrepair.scope.syntax.parser import parse  # noqa: E402

F = Path(__file__).parent / "fixtures" / "lifecycle"
CALL = re.compile(r"(\w+)\.getInstance\(\"[^\"]*\"\)")
APP, FILE = "app-1", "src/Box.java"
OPEN_KEY = Requirement("key", "field", 2, 11)
SID = scope_id(APP, FILE, "f", 10, "X.getInstance()")


def site(file: str, marker: str) -> dict:
    lines = (F / file).read_text().splitlines()
    n = next(i for i, t in enumerate(lines, 1) if t.rstrip().endswith(f"// site: {marker}"))
    m = CALL.search(lines[n - 1])
    return {"file": file, "line": n, "call": m.group(0), "engineType": m.group(1), "resolvedAlgorithm": None,
            "resolvedProvider": None, "resolution": "resolved"}


def settled(file: str, marker: str, name: str = "key") -> Settled | None:
    text, s = (F / file).read_text(), site(file, marker)
    lc = settle(read_site(parse(text, of_file(file)), s, read_engines()), read_engines())
    return lc.origin_of(name).settled


def scope(lifecycle: Lifecycle, key_source: str = "unknown") -> Scope:
    return Scope(SID, APP, FILE, 10, "X.getInstance()", "f", 9, 20, "X", None, None, "resolved", keySource=key_source, lifecycle=lifecycle)


def lifecycle(*requirements) -> Lifecycle:
    return Lifecycle("bounded", (), "local", (), requirements)


def test_a_private_helper_that_returns_one_closed_origin_is_settled_with_its_line():
    done = settled("Vault.java", "call_key")
    lines = (F / "Vault.java").read_text().splitlines()
    assert done.origin == "keystore" and "store.getKey" in lines[done.line - 1]


def test_a_kotlin_expression_body_returns_its_expression():
    assert settled("Ledger.kt", "expression_body").origin == "literal"


def test_every_path_closing_one_way_settles():
    assert settled("Vault.java", "closed_paths").origin == "keystore"


@pytest.mark.parametrize("file, marker, name", [
    ("Vault.java", "field_key", "key"),
    ("Vault.java", "opaque_key", "key"),
    ("Ledger.kt", "returned_open", "key"),
    ("Vault.java", "public_key", "key"),
    ("Vault.java", "no_caller", "key"),
    ("Vault.java", "closed", "key"),
    ("Vault.java", "over_budget", "key"),
    ("Vault.java", "cut_path", "key"),
    ("Vault.java", "array_size", "parameters"),
    ("Vault.java", "join", "input"),
    ("Vault.java", "branch", "key"),
])
def test_what_settlement_leaves_alone(file, marker, name):
    assert settled(file, marker, name) is None


def test_a_settled_key_reaches_the_scope_document_and_its_risks():
    s = site("Vault.java", "call_key")
    scoping = build_scopes(APP, F, [s])
    found = scoping.scopes[0]
    assert found.keySource == "keystore" and "key_compatibility" in required_risks(found)
    assert validate_scopes(scoping.document(APP), scoping.lines) == []
    assert Scope.from_json(found.to_json()) == found


def test_a_closed_view_stays_and_only_an_open_one_takes_a_settled_key_origin():
    done = lifecycle(replace(OPEN_KEY, settled=Settled("generated", 3)))
    assert settled_key_source(done, "keystore") == "keystore"
    assert settled_key_source(done, "unknown") == settled_key_source(done, "parameter") == "generated"
    decoded = lifecycle(replace(OPEN_KEY, settled=Settled("decoded", 3)))
    assert settled_key_source(decoded, "unknown") == "unknown"


def test_a_settled_storage_key_declares_key_compatibility():
    assert "key_compatibility" in required_risks(scope(lifecycle(OPEN_KEY), "storage"))


def test_site_replace_shows_what_code_settled():
    text = "\n".join(_lifecycle(scope(lifecycle(replace(OPEN_KEY, settled=Settled("keystore", 4))))))
    assert "key: field (line 2), taken at line 11; settled: keystore, line 4" in text


@pytest.mark.parametrize("requirement, problem", [
    (replace(OPEN_KEY, settled=Settled("guess", 3)), "settled origin 'guess'"),
    (replace(OPEN_KEY, settled=Settled("field", 3)), "settled origin 'field'"),
    (replace(OPEN_KEY, settled=Settled("keystore", 99)), "settled cites line 99"),
    (Requirement("input", "literal", 9, 12, (), Settled("literal", 3)), "settled over the closed origin 'literal'"),
])
def test_the_scopes_validator_refuses(requirement, problem):
    doc = {"schemaVersion": 4, "app": APP, "scopes": [scope(lifecycle(requirement)).to_json()], "unscoped": []}
    assert any(problem in p for p in validate_scopes(doc, {FILE: 40}))


def test_the_scopes_validator_refuses_a_settled_of_another_shape():
    row = {**vars(OPEN_KEY), "depth1": [], "settled": {"origin": "keystore", "line": 3, "source": "code"}}
    doc = {"schemaVersion": 4, "app": APP, "unscoped": [], "scopes": [{**scope(lifecycle()).to_json(),
                                                                       "lifecycle": {**lifecycle().to_json(), "requirements": [row]}}]}
    assert any("settled is not {origin, line}" in p for p in validate_scopes(doc, {FILE: 40}))


def test_a_public_key_from_an_app_wrapper_is_the_wrappers_not_a_key_stores():
    text = ("class Fp { Store store;\n void f() {\n byte[] k = this.store.getPublicKey();\n"
            " MessageDigest md = MessageDigest.getInstance(\"H\");\n md.update(k);\n md.digest();\n }\n}\n")
    s = {"file": "Fp.java", "line": 4, "call": 'MessageDigest.getInstance("H")', "engineType": "MessageDigest",
         "resolvedAlgorithm": None, "resolvedProvider": None, "resolution": "resolved"}
    lc = read_site(parse(text, of_file("Fp.java")), s, read_engines())
    assert lc.lifecycle.origin_of("input").origin == "field"
