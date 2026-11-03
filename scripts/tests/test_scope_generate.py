import pathlib, shutil, sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scope_generate, scope_harness, scope_wrapper  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures/scoped"
GENERATED = pathlib.PurePosixPath(scope_wrapper.FOLDER)


def run(tmp_path, harness="harness.yaml", compiler=lambda root: []):
    plan, compiled = scope_generate.generate(FIXTURES / harness, tmp_path / "root", tmp_path / "out", compiler=compiler)
    return yaml.safe_load(plan.read_text()), compiled


def generated(tmp_path):
    folder = tmp_path / "root" / GENERATED
    return {p.relative_to(folder).as_posix(): p.read_text() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_java_wrapper_is_a_public_static_member_in_its_own_variant_package(tmp_path):
    run(tmp_path)
    after = generated(tmp_path)["s0a1b2c3d4e5f/after/ScopeFunction.java"]
    assert after.startswith("package io.github.junekim0007.cryptobench.scoped.s0a1b2c3d4e5f.after;\n")
    assert "import javax.crypto.Cipher;" in after
    assert "    public static byte[] encrypt(byte[] plain, SecretKey key) throws Exception {" in after
    assert '"AndroidOpenSSL"' in after
    assert '"AndroidOpenSSL"' not in generated(tmp_path)["s0a1b2c3d4e5f/before/ScopeFunction.java"]


def test_kotlin_wrapper_drops_visibility_inside_an_object(tmp_path):
    run(tmp_path)
    before = generated(tmp_path)["s2c3d4e5f6071/before/ScopeFunction.kt"]
    assert before.startswith("package io.github.junekim0007.cryptobench.scoped.s2c3d4e5f6071.before\n")
    assert "object ScopeFunction {" in before
    assert '    fun digest(data: ByteArray): ByteArray = MessageDigest.getInstance("SHA-256").digest(data)' in before


def test_catalog_synthesises_seeded_inputs_and_pairs_encrypt_with_decrypt(tmp_path):
    plan, compiled = run(tmp_path)
    catalog = generated(tmp_path)["GeneratedScopes.kt"]
    assert compiled == ["0a1b2c3d4e5f", "1b2c3d4e5f60", "2c3d4e5f6071"]
    assert 'ScopeInputs.secretKey("AES", 256, 8)' in catalog and "ScopeInputs.bytes(1024, 7)" in catalog
    assert "val artifactB = lazy {" in catalog and "val artifactA = lazy {" in catalog
    interop = {s["id"]: s["interop"] for s in plan["scopes"]}
    assert interop["0a1b2c3d4e5f"] == {"check": "round_trip", "partner": "1b2c3d4e5f60", "role": "produce"}
    assert interop["1b2c3d4e5f60"]["role"] == "consume"
    assert interop["2c3d4e5f6071"] == {"check": "same_output"}


def test_generation_is_deterministic(tmp_path):
    run(tmp_path / "one")
    run(tmp_path / "two")
    assert generated(tmp_path / "one") == generated(tmp_path / "two")
    assert (tmp_path / "one/out/scoped-plan.yaml").read_text() == (tmp_path / "two/out/scoped-plan.yaml").read_text()


def test_unsupported_parameters_and_unsatisfied_dependencies_are_not_compilable(tmp_path):
    def compiler(root):
        failing = (root / GENERATED / "s5f60718293a4").exists()
        return [f"{GENERATED}/s5f60718293a4/before/ScopeFunction.java:2: error: incompatible types"] if failing else []
    plan, compiled = run(tmp_path, "broken.yaml", compiler)
    scopes = {s["id"]: s for s in plan["scopes"]}
    assert scopes["3d4e5f607182"]["status"] == "not_compilable"
    assert scopes["3d4e5f607182"]["reason"] == "unsupported_parameter: context: Context"
    assert scopes["4e5f60718293"]["reason"] == "unsatisfied_dependencies"
    assert scopes["4e5f60718293"]["identifiers"] == ["cipherFor", "KEY_ALIAS"]
    assert scopes["5f60718293a4"]["reason"] == "compile_error"
    assert scopes["5f60718293a4"]["compilerErrors"][0].endswith("incompatible types")
    assert compiled == ["2c3d4e5f6071"]
    assert sorted(generated(tmp_path)) == ["GeneratedScopes.kt", "s2c3d4e5f6071/after/ScopeFunction.kt", "s2c3d4e5f6071/before/ScopeFunction.kt"]


def test_a_failure_outside_the_generated_sources_stops_the_run(tmp_path):
    with pytest.raises(scope_generate.GenerateError, match="harness_build_failed"):
        run(tmp_path, compiler=lambda root: ["e: modules/android/src/androidTest/kotlin/Other.kt:1:1 broken"])


def test_clean_removes_the_generated_folder(tmp_path):
    run(tmp_path)
    scope_generate.clean(tmp_path / "root")
    assert not (tmp_path / "root" / GENERATED).exists()


def test_the_current_item_rides_next_to_the_option_into_the_plan(tmp_path):
    plan, _ = run(tmp_path)
    first = plan["scopes"][0]
    assert (first["current"], first["option"]) == ("Cipher|AES/GCM/NoPadding|BC", "Cipher|AES/GCM/NoPadding|AndroidOpenSSL")


def harness_with(tmp_path, inputs):
    for source in FIXTURES.iterdir():
        (tmp_path / source.name).write_text(source.read_text())
    text = (FIXTURES / "harness.yaml").read_text().replace("inputs: {inputSize: 1024, keySize: 256, from: run}", inputs, 1)
    (tmp_path / "harness.yaml").write_text(text)
    return tmp_path / "harness.yaml"


def test_a_null_run_size_is_missing_input_naming_its_source(tmp_path):
    path = harness_with(tmp_path, "inputs: {inputSize: null, keySize: 256, from: run}")
    plan, _ = scope_generate.generate(path, tmp_path / "root", tmp_path / "out", compiler=lambda _: [])
    first = yaml.safe_load(plan.read_text())["scopes"][0]
    assert (first["status"], first["reason"]) == ("not_compilable", "missing_input: inputSize for plain, none from run")
    assert first["inputs"] == {"inputSize": None, "keySize": 256, "from": "run"}


def test_inputs_without_a_source_are_refused(tmp_path):
    path = harness_with(tmp_path, "inputs: {inputSize: 1024, keySize: 256}")
    with pytest.raises(scope_harness.HarnessError, match="inputs.from None"):
        scope_harness.read(path)


def test_a_not_measurable_scope_is_recorded_and_never_generated(tmp_path):
    shutil.copytree(FIXTURES, tmp_path / "fixtures")
    path = tmp_path / "fixtures/harness.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["scopes"][2]["notMeasurable"] = "no_operation"
    path.write_text(yaml.safe_dump(doc))
    plan, compiled = scope_generate.generate(path, tmp_path / "root", tmp_path / "out", compiler=lambda root: [])
    record = yaml.safe_load(plan.read_text())["scopes"][2]
    assert (record["status"], record["reason"]) == ("not_measurable", "no_operation")
    assert "2c3d4e5f6071" not in compiled and not (tmp_path / "root" / GENERATED / "s2c3d4e5f6071").exists()
