import pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scope import dependencies as scope_dependencies  # noqa: E402
from scope import interop as scope_interop  # noqa: E402
from scope import languages as scope_languages  # noqa: E402
from scope import signature as scope_signature  # noqa: E402
from scope.signature import Parameter  # noqa: E402


def test_java_header_keeps_the_body_and_strips_annotations():
    source = '@Override\nprivate synchronized String hash(@NonNull final byte[] data, String salt) throws Exception {\n    return "//" + salt;\n}\n'
    signature = scope_languages.of("java").parse(source)
    assert signature.name == "hash"
    assert signature.parameters == (Parameter("data", "byte[]"), Parameter("salt", "String"))
    assert signature.returns == "String"
    assert signature.member.startswith("public static String hash(byte[] data, String salt) throws Exception {")
    assert '"//" + salt' in signature.member


def test_kotlin_block_body_returns_unit_and_expression_body_is_inferred():
    assert scope_languages.of("kotlin").parse("fun log(data: ByteArray) {\n}\n").returns is None
    assert scope_languages.of("kotlin").parse("internal fun twice(data: ByteArray) = data + data").returns == scope_signature.INFERRED


@pytest.mark.parametrize("source, language, reason", [
    ("suspend fun load(data: ByteArray): ByteArray = data", "kotlin", "suspend_function"),
    ("fun ByteArray.sealed(): ByteArray = this", "kotlin", "extension_function"),
    ("fun <T> any(value: T): T = value", "kotlin", "generic_function"),
    ("public static byte[] join(byte[]... parts) { return null; }", "java", "vararg_parameter"),
    ("class Holder { void run() {} }", "java", "not_a_function"),
])
def test_unsupported_shapes_name_their_reason(source, language, reason):
    with pytest.raises(scope_signature.SignatureError, match=reason):
        scope_languages.of(language).parse(source)


def test_dependencies_resolve_by_import_language_or_the_tag_stub():
    resolution = scope_dependencies.resolve(["Cipher", "String", "TAG", "helper"], ["import javax.crypto.Cipher;"], "java")
    assert resolution.unsatisfied == ("helper",)
    assert resolution.stubs == ('private static final String TAG = "scope";',)
    assert scope_dependencies.resolve(["helper"], ["import com.example.*"], "kotlin").deferred == ("helper",)


def test_interop_pairs_only_an_inverse_whose_types_line_up():
    encrypt = scope_languages.of("kotlin").parse("fun encryptNote(note: String, key: SecretKey): ByteArray = error(\"x\")")
    decrypt = scope_languages.of("kotlin").parse("fun decryptNote(sealed: ByteArray, key: SecretKey): String = error(\"x\")")
    wrong = scope_languages.of("kotlin").parse("fun decryptNote(sealed: String, key: SecretKey): String = error(\"x\")")
    linked = {"a": {"partner": "b", "role": "produce"}, "b": {"partner": "a", "role": "consume"}}
    assert scope_interop.plan({"a": encrypt, "b": decrypt}, linked)["a"].index == 0
    assert scope_interop.plan({"a": encrypt, "b": decrypt}, linked)["b"].index == 0
    assert scope_interop.plan({"a": encrypt, "b": wrong}, linked)["a"].check == "same_output"


def test_interop_pairs_by_link_never_by_name():
    encrypt = scope_languages.of("kotlin").parse("fun encryptNote(note: String, key: SecretKey): ByteArray = error(\"x\")")
    decrypt = scope_languages.of("kotlin").parse("fun decryptNote(sealed: ByteArray, key: SecretKey): String = error(\"x\")")
    other = scope_languages.of("kotlin").parse("fun readBack(sealed: ByteArray, key: SecretKey): String = error(\"x\")")
    assert scope_interop.plan({"a": encrypt, "b": decrypt}, {})["a"].check == "same_output"
    linked = {"a": {"partner": "b", "role": "produce"}, "b": {"partner": "a", "role": "consume"}}
    plan = scope_interop.plan({"a": encrypt, "b": other}, linked)
    assert (plan["a"].check, plan["a"].partner, plan["b"].role) == ("round_trip", "b", "consume")
    assert scope_interop.plan({"a": encrypt}, {"a": {"partner": "gone", "role": "produce"}})["a"].check == "same_output"


def test_a_java_wrapper_lets_any_exception_leave_so_a_swap_that_adds_a_checked_one_still_compiles():
    declared = "byte[] f(byte[] a)\n    throws A,\n    B {\n  return a;\n}\n"
    assert scope_signature.java(declared).member == "public static byte[] f(byte[] a) throws Exception {\n  return a;\n}"
    assert scope_signature.java("void g() { }\n").member == "public static void g() throws Exception { }"
