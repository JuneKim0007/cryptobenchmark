import re
from pathlib import Path

import pytest

from perfrepair.dto.lifecycle import Lifecycle
from perfrepair.scope.engines import read_engines
from perfrepair.source.language import of_file

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_java")
pytest.importorskip("tree_sitter_kotlin")

from perfrepair.scope.lifecycle.read import lifecycle_of  # noqa: E402
from perfrepair.scope.syntax.parser import parse  # noqa: E402

F = Path(__file__).parent / "fixtures" / "lifecycle"
CALL = re.compile(r"(\w+)\.getInstance\(\"[^\"]*\"\)")


def read(file: str, marker: str) -> Lifecycle:
    text = (F / file).read_text()
    line = next(n for n, t in enumerate(text.splitlines(), 1) if t.rstrip().endswith(f"// site: {marker}"))
    m = CALL.search(text.splitlines()[line - 1])
    site = {"line": line, "call": m.group(0), "engineType": m.group(1)}
    return lifecycle_of(parse(text, of_file(file)), site, read_engines())


def steps(lc: Lifecycle) -> list[tuple]:
    return [(s.role, s.call, s.where) for s in lc.steps]


@pytest.mark.parametrize("file, marker, status, reasons, binding", [
    ("Box.java", "local", "bounded", (), "local"),
    ("Box.java", "chain", "bounded", (), "chain"),
    ("Box.java", "returned", "partially_bounded", ("escape", "depth1"), "returned"),
    ("Box.java", "field", "partially_bounded", ("field", "depth1"), "field"),
    ("Box.java", "wrapper", "partially_bounded", ("wrapper",), "local"),
    ("Box.java", "no_real_use", "no_real_use", (), "discarded"),
    ("Box.java", "argument", "partially_bounded", ("escape", "depth1"), "argument"),
    ("Seal.kt", "lazy_field", "partially_bounded", ("field", "depth1"), "field"),
    ("Seal.kt", "apply", "bounded", (), "local"),
    ("Seal.kt", "chain", "bounded", (), "chain"),
    ("Seal.kt", "with", "bounded", (), "chain"),
    ("Seal.kt", "deferred", "partially_bounded", ("deferred",), "local"),
    ("Seal.kt", "no_real_use", "no_real_use", (), "local"),
    ("Seal.kt", "engine_unknown", "unsupported", ("engine_unknown",), None),
])
def test_status_reasons_and_binding(file, marker, status, reasons, binding):
    lc = read(file, marker)
    assert (lc.status, lc.reasons, lc.binding) == (status, reasons, binding)


def test_local_steps_requirements_and_operation_come_from_the_engine_table():
    lc = read("Box.java", "local")
    assert steps(lc) == [("configure", "init", "same"), ("use", "doFinal", "same")]
    assert [(r.name, r.origin, r.line, r.at) for r in lc.requirements] == [("key", "parameter", 10, 12),
                                                                            ("input", "parameter", 10, 13)]
    assert lc.operations == ("DECRYPT",)


def test_a_field_is_followed_into_its_other_methods_one_away():
    lc = read("Box.java", "field")
    assert steps(lc) == [("configure", "init", "same"), ("use", "doFinal", "depth1")]
    assert lc.operations == ("ENCRYPT",)


def test_a_helper_return_is_followed_to_its_same_class_caller():
    lc = read("Box.java", "returned")
    assert steps(lc) == [("configure", "init", "depth1"), ("use", "doFinal", "depth1")]
    assert [(r.name, r.origin) for r in lc.requirements] == [("key", "literal"), ("input", "parameter")]


def test_a_known_consumer_is_a_use_and_a_callee_is_read_one_away():
    assert ("consume", "CipherOutputStream", "same") in steps(read("Box.java", "wrapper"))
    assert steps(read("Box.java", "argument")) == [("use", "digest", "depth1")]


def test_kotlin_scope_functions_act_on_the_object():
    lc = read("Seal.kt", "apply")
    assert steps(lc) == [("configure", "init", "same"), ("use", "doFinal", "same")]
    assert [(r.name, r.origin) for r in lc.requirements][0] == ("key", "field")
    assert steps(read("Seal.kt", "with")) == [("use", "digest", "same")]


def test_an_unread_call_is_unsupported_with_its_reason():
    text = (F / "Seal.kt").read_text()
    lc = lifecycle_of(parse(text, of_file("Seal.kt")), {"line": 1, "call": "Cipher.getInstance(\"Z\")",
                                                         "engineType": "Cipher"}, read_engines())
    assert (lc.status, lc.reasons) == ("unsupported", ("call_not_found",))


def test_the_lifecycle_round_trips_through_json():
    lc = read("Box.java", "field")
    assert Lifecycle.from_json(lc.to_json()) == lc
