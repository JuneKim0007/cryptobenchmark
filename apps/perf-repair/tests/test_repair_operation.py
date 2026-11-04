import pytest

from perfrepair.dto.site import Scope
from perfrepair.repair.operation import has_operation
from perfrepair.source import language
from perfrepair.source.code import Code

CALL = 'MessageDigest.getInstance("MD5")'


def check(body: str, lang=language.JAVA) -> bool:
    text = "class A {\n" + body + "}\n"
    lines = text.splitlines()
    line = next(i for i, l in enumerate(lines, 1) if "getInstance(" in l)
    scope = Scope("0" * 12, "demo", "A.java", line, CALL, "f", 2, len(lines) - 1, "MessageDigest", "MD5", None, "default")
    return has_operation(Code.of(text, lang), scope)


@pytest.mark.parametrize("body", [
    "MessageDigest f() throws Exception {\n  return MessageDigest.getInstance(\"MD5\");\n}\n",
    "MessageDigest f() throws Exception {\n  MessageDigest md = MessageDigest.getInstance(\"MD5\");\n  md.reset();\n  return md;\n}\n",
    "void f() {\n  try {\n    MessageDigest md = MessageDigest.getInstance(\"MD5\");\n  } catch (Exception e) {\n    log(e);\n  }\n}\n",
    "void f() throws Exception {\n  hmac = MessageDigest.getInstance(\"MD5\");\n  hmac.reset();\n}\n",
], ids=["returned", "setup_only", "dead_local", "field_setup_only"])
def test_a_function_that_only_creates_or_configures_has_no_operation(body):
    assert not check(body)


@pytest.mark.parametrize("body", [
    "byte[] f(byte[] in) throws Exception {\n  MessageDigest md = MessageDigest.getInstance(\"MD5\");\n  md.reset();\n  return md.digest(in);\n}\n",
    "byte[] f(byte[] in) throws Exception {\n  return MessageDigest.getInstance(\"MD5\").digest(in);\n}\n",
    "byte[] f(byte[] in) throws Exception {\n  MessageDigest md = MessageDigest.getInstance(\"MD5\");\n  return run(md, in);\n}\n",
    "void f() throws Exception {\n  md = MessageDigest.getInstance(\"MD5\");\n  compute();\n}\n",
    "byte[] f(int k, byte[] in) throws Exception {\n  MessageDigest d;\n  switch (k) {\n  case 1:\n    d = MessageDigest.getInstance(\"MD5\");\n"
    "    break;\n  default:\n    throw new IllegalStateException();\n  }\n  return d.digest(in);\n}\n",
], ids=["local_op", "chained", "handed_to_call", "field_then_own_method", "case_label_above"])
def test_an_operation_on_the_primitive_counts(body):
    assert check(body)


def test_a_kotlin_scope_block_operates_through_its_top_level_calls():
    kotlin = "fun f(b: ByteArray): ByteArray =\n  MessageDigest.getInstance(\"MD5\").run {\n    reset()\n    digest(b)\n  }\n"
    assert check(kotlin, language.KOTLIN)
    assert not check(kotlin.replace("    digest(b)\n", ""), language.KOTLIN)
