from perfrepair.repair.dependencies import dependencies, load, tokens
from perfrepair.source import language


def test_a_numeric_literal_is_one_token():
    assert tokens("x & 0xff | 0b1010 + 10L * 1.5e-3f + 0..n") == \
        ["x", "&", "0xff", "|", "0b1010", "+", "10L", "*", "1.5e-3f", "+", "0", ".", ".", "n"]
    f = "int f(int x) {\n  return x & 0xFF;\n}\n"
    assert dependencies(f, language.JAVA, [], load("java")) == []


def test_java_lang_needs_no_import():
    f = "void f() {\n  StringBuffer s = new StringBuffer();\n  throw new AssertionError(s);\n}\n"
    assert dependencies(f, language.JAVA, [], load("java")) == []
