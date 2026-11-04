import json
from pathlib import Path

import pytest

from perfrepair.app.__main__ import main
from perfrepair.scope.extract import enclosing, functions
from perfrepair.dto.lifecycle import Lifecycle, Requirement
from perfrepair.scope.engines import read_engines
from perfrepair.scope.facts import key_source, key_source_view, read_patterns, sinks
from perfrepair.source.language import JAVA, KOTLIN
from perfrepair.source.code import Code
from perfrepair.validation.app import validate_app_facts, validate_scopes
from perfrepair.check.run import validate_run
from perfrepair.screen.catalog import screening_catalog
from helpers import with_results
from perfrepair.app.facts.path_id import path_id

F = Path(__file__).parent / "fixtures"
MANIFEST = F / "results" / "test-api36-00000000" / "manifest.yaml"
DEMO = path_id(F / "app")


def _fn(text: str, language, needle: str = "getInstance"):
    code = Code.of(text, language)
    fn = enclosing(functions(code), code.text.index(needle))
    return code, fn


def _span(code, fn):
    return fn.name, code.line(fn.start), code.line(fn.end - 1)


@pytest.fixture
def scopes(tmp_path):
    assert main(["--app", str(F / "app"), "--device-results", str(with_results(tmp_path))]) == 0
    return tmp_path, json.loads((tmp_path / DEMO / "scopes.json").read_text())


def test_java_method_span_includes_annotations_and_skips_control_blocks():
    code, fn = _fn("class A {\n  int x;\n  @Override\n  public byte[] f(byte[] in, int n) throws Exception {\n"
                   "    if (n > 0) { return C.getInstance(\"x\"); }\n    return null;\n  }\n}\n", JAVA)
    assert _span(code, fn) == ("f", 3, 7) and fn.params == ("in", "n")


def test_java_anonymous_class_method_is_the_enclosing_function():
    code, fn = _fn("class A {\n void outer() {\n  Runnable r = new Runnable() {\n   public void run() {\n"
                   "    C.getInstance(\"x\");\n   }\n  };\n }\n}\n", JAVA)
    assert _span(code, fn) == ("run", 4, 6)


def test_java_initializer_has_no_function():
    code, fn = _fn("class A {\n static { C.getInstance(\"x\"); }\n Object f = C.getInstance(\"y\");\n}\n", JAVA)
    assert fn is None


def test_kotlin_expression_bodied_fun_spans_its_continuation_lines():
    code, fn = _fn("class A {\n  fun f(b: ByteArray) =\n    C.getInstance(\"x\")\n      .digest(b)\n"
                   "  fun g() = 1\n}\n", KOTLIN)
    assert _span(code, fn) == ("f", 2, 4) and fn.expression


def test_kotlin_lambda_belongs_to_its_function_and_modifiers_start_it():
    code, fn = _fn("class A {\n  @Throws(E::class)\n  private suspend fun <T> List<T>.f(): () -> Any {\n"
                   "    val m = { C.getInstance(\"x\") }\n    return m\n  }\n}\n", KOTLIN)
    assert _span(code, fn) == ("f", 2, 6)


def test_kotlin_property_and_abstract_fun_are_not_functions():
    code, fn = _fn("interface I {\n  fun a(x: Int): Int\n}\nclass A {\n  val c = C.getInstance(\"x\")\n}\n", KOTLIN)
    assert fn is None and [f.name for f in functions(code)] == []


def test_kotlin_secondary_constructor_but_not_primary():
    code = Code.of("class A constructor(x: Int) {\n  constructor() : this(1) {\n    C.getInstance(\"x\")\n  }\n}\n", KOTLIN)
    assert [f.name for f in functions(code)] == ["constructor"]
    assert _span(code, enclosing(functions(code), code.text.index("C.get"))) == ("constructor", 2, 4)


@pytest.mark.parametrize("body, language, expected_sinks, expected_key", [
    ("fun f(k: Key) { c.init(1, k); prefs.edit().putString(\"a\", c.doFinal()).apply() }", KOTLIN,
     ("persist",), "parameter"),
    ("void f(Socket s) { c.init(1, new SecretKeySpec(new byte[]{1}, \"A\")); s.getOutputStream().write(x); }",
     JAVA, ("network",), "literal"),
    ("fun f() = KeyGenerator.getInstance(\"A\").generateKey()", KOTLIN, ("return",), "generated"),
    ("void f(char[] p) { SecretKeyFactory.getInstance(\"P\").generateSecret(new PBEKeySpec(p)); }", JAVA,
     ("local",), "derived"),
    ("void f() { this.out = c.doFinal(); }", JAVA, ("unknown",), "unknown"),
    ("void f() { out = c.doFinal(); }", JAVA, ("unknown",), "unknown"),
    ("fun f() { hash = md.digest(x); return }", KOTLIN, ("unknown",), "unknown"),
    ("void f(byte[] a) { byte[] out; out = md.digest(a); a[0] = 1; int n = 0; n += 1; }", JAVA, ("local",), "unknown"),
    ("fun f(): ByteArray { var h: ByteArray; h = md.digest(); return h }", KOTLIN, ("return",), "unknown"),
])
def test_sinks_and_key_sources(body, language, expected_sinks, expected_key):
    code = Code.of(body, language)
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
    assert main(["--app", str(F / "app"), "--device-results", str(with_results(again))]) == 0
    for name in ("sites.json", "app.json", "scopes.json"):
        assert (run / DEMO / name).read_bytes() == (again / DEMO / name).read_bytes()


def test_validators_catch_a_tampered_scope_and_app(scopes):
    _, doc = scopes
    assert validate_scopes(doc) == []
    doc["scopes"][0]["line"] += 1000
    doc["scopes"][1]["sinks"] = ["nowhere"]
    problems = validate_scopes(doc)
    assert any("id is not scope_id" in p for p in problems) and any("outside" in p for p in problems)
    assert any("sinks" in p for p in problems)
    assert validate_app_facts({"schemaVersion": 1, "app": "a", "pathId": "a", "root": "r", "projectRoot": ".", "bundled": [{"artifact": 1}],
                               "registers": [], "minSdk": "24", "targetSdk": None}) == [
        "app.json: minSdk is not int or null", "bundled[0]: artifact is not str"]
    assert validate_app_facts({"schemaVersion": 1, "app": "a", "pathId": "a", "root": "r", "bundled": [], "registers": []}) == [
        "app.json: projectRoot is not str"]


def test_validate_run_reads_app_folders(scopes):
    from perfrepair.data_handler.inbound.__main__ import main as inbound
    run, _ = scopes
    assert inbound(["--device-results", str(with_results(run))]) == 0
    result = validate_run(run, screening_catalog(None))
    assert result[f"{DEMO}/scopes.json"] == [] and result[f"{DEMO}/app.json"] == []


GOOD_LIFECYCLE = {"status": "partially_bounded", "reasons": ["field"], "binding": "field",
                  "steps": [{"role": "use", "call": "f", "line": 4, "where": "depth1"}],
                  "requirements": [{"name": "key", "origin": "field", "line": 2, "at": 4, "depth1": ["generated"]}],
                  "operations": ["OP1"]}


@pytest.mark.parametrize("change, problem", [
    ({"status": "done"}, "status 'done'"),
    ({"status": "bounded"}, "reason 'field' is not one of () for bounded"),
    ({"reasons": []}, "partially_bounded without a reason"),
    ({"binding": "somewhere"}, "binding 'somewhere'"),
    ({"steps": [{"role": "read", "call": "f", "line": 4, "where": "same"}]}, "role 'read'"),
    ({"requirements": [{"name": "key", "origin": "guess", "line": 2, "at": 4, "depth1": []}]}, "origin 'guess'"),
    ({"steps": [{"role": "use", "call": "f", "line": 99, "where": "same"}]}, "cites line 99"),
])
def test_a_lifecycle_outside_its_closed_lists_or_its_file_is_refused(scopes, change, problem):
    _, doc = scopes
    s = doc["scopes"][0]
    s["lifecycle"] = {**GOOD_LIFECYCLE, **change}
    assert any(problem in p for p in validate_scopes(doc, {s["file"]: 40}))
    s.update(lifecycle=GOOD_LIFECYCLE, pattern="fixed", patternReason="held_in_field", patternLines=[4])
    assert validate_scopes(doc, {s["file"]: 40}) == []


def test_scopes_without_a_lifecycle_or_of_the_old_schema_are_refused(scopes):
    _, doc = scopes
    doc["scopes"][0]["lifecycle"] = None
    assert any("no lifecycle" in p for p in validate_scopes(doc))
    assert validate_scopes({**doc, "schemaVersion": 1})[0] == "schemaVersion 1"


def test_the_engine_table_loads_and_a_bad_one_is_refused(tmp_path):
    engines = read_engines()
    assert engines.factory and all(e.terminal for e in engines.engines.values())
    bad = tmp_path / "engines.yaml"
    bad.write_text("schemaVersion: 1\nfactory: make\nengines:\n  E:\n    terminal: [go]\n    requirements: {stop: {0: key}}\n"
                   "    operations: {call: {walk: OP}}\norigins: {guessed: [x]}\nspecs: {}\naccessors: []\ndecoders: []\n")
    with pytest.raises(ValueError) as e:
        read_engines(bad)
    assert all(p in str(e.value) for p in ("requirement call stop", "outside its lifecycle", "origin guessed"))


def test_the_key_source_view_prefers_the_key_origin_and_falls_back_to_the_patterns():
    def lc(origin, depth1=()):
        return Lifecycle("bounded", binding="local", requirements=(Requirement("key", origin, 1, 2, depth1),))
    assert key_source_view(lc("keystore"), "unknown") == "keystore"
    assert key_source_view(lc("field", ("generated",)), "unknown") == "generated"
    assert key_source_view(lc("parameter", ("keystore",)), "parameter") == "keystore"
    assert key_source_view(lc("other_call"), "derived") == "derived"
    assert key_source_view(None, "literal") == "literal"
