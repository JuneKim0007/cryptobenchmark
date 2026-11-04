import importlib
from pathlib import Path

import pytest

from perfrepair.scope.build import build_scopes
from perfrepair.scope.syntax import parser
from perfrepair.source.language import JAVA, KOTLIN

ROOT = Path(__file__).parents[1] / "src" / "perfrepair"
SITE = {"file": "Box.java", "line": 3, "call": "Cipher.getInstance(\"A\")", "engineType": "Cipher",
        "resolvedAlgorithm": "A", "resolvedProvider": "P", "resolution": "default"}
BOX = "class Box {\n  byte[] f(byte[] d, Key k) throws Exception {\n    Cipher c = Cipher.getInstance(\"A\");\n" \
      "    c.init(Cipher.ENCRYPT_MODE, k);\n    return c.doFinal(d);\n  }\n}\n"


@pytest.fixture
def no_parser(monkeypatch):
    real = importlib.import_module

    def refuse(name, *a, **kw):
        if name.startswith("tree_sitter"):
            raise ImportError(f"No module named {name!r}")
        return real(name, *a, **kw)

    parser._parser.cache_clear()
    monkeypatch.setattr(importlib, "import_module", refuse)
    yield
    parser._parser.cache_clear()


def test_a_missing_parser_is_raised_never_read_another_way(no_parser):
    assert parser.available() is False
    with pytest.raises(parser.ParserMissing):
        parser.parse("class A {}", JAVA)


def test_a_missing_parser_makes_every_lifecycle_unsupported_and_keeps_the_scope(no_parser, tmp_path):
    (tmp_path / "Box.java").write_text(BOX)
    scoping = build_scopes("demo", tmp_path, [SITE])
    [scope] = scoping.scopes
    assert (scope.lifecycle.status, scope.lifecycle.reasons) == ("unsupported", ("parser_missing",))
    assert (scope.function, scope.start, scope.end) == ("f", 2, 6) and scoping.statuses() == {"unsupported": 1}


def test_with_the_parser_the_same_site_is_bounded(tmp_path):
    pytest.importorskip("tree_sitter_java")
    (tmp_path / "Box.java").write_text(BOX)
    [scope] = build_scopes("demo", tmp_path, [SITE]).scopes
    assert scope.lifecycle.status == "bounded" and [t.call for t in scope.lifecycle.steps] == ["init", "doFinal"]


def test_nodes_carry_neutral_kinds_lines_and_no_comments():
    pytest.importorskip("tree_sitter_kotlin")
    root = parser.parse("// c\nfun f() = A.b(1)\n", KOTLIN)
    kinds = [(n.kind, n.line) for n in root.walk() if n.kind in ("call", "method", "literal")]
    assert kinds == [("method", 2), ("call", 2), ("literal", 2)]
    assert all(n.type not in ("line_comment", "comment") for n in root.walk())


def test_only_the_syntax_package_names_the_parser():
    users = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py")
                   if "tree_sitter" in p.read_text() and p.relative_to(ROOT).parts[:2] != ("scope", "syntax"))
    assert users == []
