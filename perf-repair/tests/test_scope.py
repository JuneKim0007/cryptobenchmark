import json
from pathlib import Path

import pytest

from perfrepair.app.__main__ import main
from perfrepair.app.lexer import Code
from perfrepair.scope.extract import enclosing, functions
from perfrepair.scope.facts import key_source, read_patterns, sinks
from perfrepair.validation.app import validate_app_facts, validate_scopes
from perfrepair.validation.run import validate_run

F = Path(__file__).parent / "fixtures"
MANIFEST = F / "results" / "manifest.yaml"


def _fn(text: str, kotlin: bool, needle: str = "getInstance"):
    code = Code.of(text, kotlin)
    fn = enclosing(functions(code), code.text.index(needle))
    return code, fn


def _span(code, fn):
    return fn.name, code.line(fn.start), code.line(fn.end - 1)


@pytest.fixture
def scopes(tmp_path):
    assert main(["--manifest", str(MANIFEST), "--app", str(F / "app"), "--run", str(tmp_path), "--name", "demo"]) == 0
    return tmp_path, json.loads((tmp_path / "apps" / "demo" / "scopes.json").read_text())


def test_java_method_span_includes_annotations_and_skips_control_blocks():
    code, fn = _fn("class A {\n  int x;\n  @Override\n  public byte[] f(byte[] in, int n) throws Exception {\n"
                   "    if (n > 0) { return C.getInstance(\"x\"); }\n    return null;\n  }\n}\n", False)
    assert _span(code, fn) == ("f", 3, 7) and fn.params == ("in", "n")


def test_java_anonymous_class_method_is_the_enclosing_function():
    code, fn = _fn("class A {\n void outer() {\n  Runnable r = new Runnable() {\n   public void run() {\n"
                   "    C.getInstance(\"x\");\n   }\n  };\n }\n}\n", False)
    assert _span(code, fn) == ("run", 4, 6)


def test_java_initializer_has_no_function():
    code, fn = _fn("class A {\n static { C.getInstance(\"x\"); }\n Object f = C.getInstance(\"y\");\n}\n", False)
    assert fn is None


def test_kotlin_expression_bodied_fun_spans_its_continuation_lines():
    code, fn = _fn("class A {\n  fun f(b: ByteArray) =\n    C.getInstance(\"x\")\n      .digest(b)\n"
                   "  fun g() = 1\n}\n", True)
    assert _span(code, fn) == ("f", 2, 4) and fn.expression


def test_kotlin_lambda_belongs_to_its_function_and_modifiers_start_it():
    code, fn = _fn("class A {\n  @Throws(E::class)\n  private suspend fun <T> List<T>.f(): () -> Any {\n"
                   "    val m = { C.getInstance(\"x\") }\n    return m\n  }\n}\n", True)
    assert _span(code, fn) == ("f", 2, 6)


def test_kotlin_property_and_abstract_fun_are_not_functions():
    code, fn = _fn("interface I {\n  fun a(x: Int): Int\n}\nclass A {\n  val c = C.getInstance(\"x\")\n}\n", True)
    assert fn is None and [f.name for f in functions(code)] == []


def test_kotlin_secondary_constructor_but_not_primary():
    code = Code.of("class A constructor(x: Int) {\n  constructor() : this(1) {\n    C.getInstance(\"x\")\n  }\n}\n", True)
    assert [f.name for f in functions(code)] == ["constructor"]
    assert _span(code, enclosing(functions(code), code.text.index("C.get"))) == ("constructor", 2, 4)


@pytest.mark.parametrize("body, kotlin, expected_sinks, expected_key", [
    ("fun f(k: Key) { c.init(1, k); prefs.edit().putString(\"a\", c.doFinal()).apply() }", True,
     ("persist",), "parameter"),
    ("void f(Socket s) { c.init(1, new SecretKeySpec(new byte[]{1}, \"A\")); s.getOutputStream().write(x); }",
     False, ("network",), "literal"),
    ("fun f() = KeyGenerator.getInstance(\"A\").generateKey()", True, ("return",), "generated"),
    ("void f(char[] p) { SecretKeyFactory.getInstance(\"P\").generateSecret(new PBEKeySpec(p)); }", False,
     ("local",), "derived"),
    ("void f() { this.out = c.doFinal(); }", False, ("unknown",), "unknown"),
])
def test_sinks_and_key_sources(body, kotlin, expected_sinks, expected_key):
    code = Code.of(body, kotlin)
    [fn] = functions(code)
    assert sinks(code, fn, read_patterns()) == expected_sinks
    assert key_source(code, fn, read_patterns()) == expected_key


def test_fixture_scopes(scopes):
    _, doc = scopes
    by_line = {(s["file"].rsplit("/", 1)[-1], s["line"]): s for s in doc["scopes"]}
    vault = by_line[("Vault.kt", 22)]
    assert (vault["function"], vault["start"], vault["end"], vault["sinks"], vault["keySource"]) == \
        ("seal", 20, 27, ["persist"], "keystore")
    assert vault["call"] == "Cipher.getInstance(\n            TRANSFORM\n        )"
    digest = by_line[("Vault.kt", 30)]
    assert (digest["function"], digest["start"], digest["end"], digest["sinks"]) == ("digest", 29, 31, ["return"])
    net = by_line[("Net.java", 16)]
    assert (net["sinks"], net["keySource"], net["algorithm"]) == (["network"], "literal", "AES/GCM/NoPadding")
    assert [(u["line"], u["reason"]) for u in doc["unscoped"]] == [(18, "no_enclosing_function")]


def test_scopes_are_byte_identical_across_runs(scopes, tmp_path_factory):
    run, _ = scopes
    again = tmp_path_factory.mktemp("again")
    assert main(["--manifest", str(MANIFEST), "--app", str(F / "app"), "--run", str(again), "--name", "demo"]) == 0
    for name in ("sites.json", "app.json", "scopes.json"):
        assert (run / "apps/demo" / name).read_bytes() == (again / "apps/demo" / name).read_bytes()


def test_validators_catch_a_tampered_scope_and_app(scopes):
    _, doc = scopes
    assert validate_scopes(doc) == []
    doc["scopes"][0]["line"] += 1000
    doc["scopes"][1]["sinks"] = ["nowhere"]
    problems = validate_scopes(doc)
    assert any("id is not scope_id" in p for p in problems) and any("outside" in p for p in problems)
    assert any("sinks" in p for p in problems)
    assert validate_app_facts({"schemaVersion": 1, "app": "a", "root": "r", "bundled": [{"artifact": 1}],
                               "registers": [], "minSdk": "24", "targetSdk": None}) == [
        "app.json: minSdk is not int or null", "bundled[0]: artifact is not str"]


def test_validate_run_reads_app_folders(scopes):
    from perfrepair.data_handler.inbound.__main__ import main as inbound
    run, _ = scopes
    assert inbound(["--manifest", str(MANIFEST), "-o", str(run)]) == 0
    result = validate_run(run)
    assert result["apps/demo/scopes.json"] == [] and result["apps/demo/app.json"] == []
