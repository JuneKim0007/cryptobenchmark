import pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scope_dependencies, scope_interop, scope_signature  # noqa: E402
from scope_signature import Parameter  # noqa: E402


def test_java_header_keeps_the_body_and_strips_annotations():
    source = '@Override\nprivate synchronized String hash(@NonNull final byte[] data, String salt) throws Exception {\n    return "//" + salt;\n}\n'
    signature = scope_signature.parse(source, "java")
    assert signature.name == "hash"
    assert signature.parameters == (Parameter("data", "byte[]"), Parameter("salt", "String"))
    assert signature.returns == "String"
    assert signature.member.startswith("public static String hash(byte[] data, String salt) throws Exception {")
    assert '"//" + salt' in signature.member


def test_kotlin_block_body_returns_unit_and_expression_body_is_inferred():
    assert scope_signature.parse("fun log(data: ByteArray) {\n}\n", "kotlin").returns is None
    assert scope_signature.parse("internal fun twice(data: ByteArray) = data + data", "kotlin").returns == scope_signature.INFERRED


@pytest.mark.parametrize("source, language, reason", [
    ("suspend fun load(data: ByteArray): ByteArray = data", "kotlin", "suspend_function"),
    ("fun ByteArray.sealed(): ByteArray = this", "kotlin", "extension_function"),
    ("fun <T> any(value: T): T = value", "kotlin", "generic_function"),
    ("public static byte[] join(byte[]... parts) { return null; }", "java", "vararg_parameter"),
    ("class Holder { void run() {} }", "java", "not_a_function"),
])
def test_unsupported_shapes_name_their_reason(source, language, reason):
    with pytest.raises(scope_signature.SignatureError, match=reason):
        scope_signature.parse(source, language)


def test_dependencies_resolve_by_import_language_or_the_tag_stub():
    resolution = scope_dependencies.resolve(["Cipher", "String", "TAG", "helper"], ["import javax.crypto.Cipher;"], "java")
    assert resolution.unsatisfied == ("helper",)
    assert resolution.stubs == ('private static final String TAG = "scope";',)
    assert scope_dependencies.resolve(["helper"], ["import com.example.*"], "kotlin").deferred == ("helper",)


def test_interop_pairs_only_an_inverse_whose_types_line_up():
    encrypt = scope_signature.parse("fun encryptNote(note: String, key: SecretKey): ByteArray = error(\"x\")", "kotlin")
    decrypt = scope_signature.parse("fun decryptNote(sealed: ByteArray, key: SecretKey): String = error(\"x\")", "kotlin")
    wrong = scope_signature.parse("fun decryptNote(sealed: String, key: SecretKey): String = error(\"x\")", "kotlin")
    assert scope_interop.plan({"a": encrypt, "b": decrypt})["a"].index == 0
    assert scope_interop.plan({"a": encrypt, "b": decrypt})["b"].index == 0
    assert scope_interop.plan({"a": encrypt, "b": wrong})["a"].check == "same_output"
