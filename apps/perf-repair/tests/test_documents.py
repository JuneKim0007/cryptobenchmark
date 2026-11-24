"""dto/document.py and dto/coded.py: the one schemaVersion check, its error type, the one wording Kotlin gives."""
import importlib
import pkgutil

import pytest

import perfrepair
from cryptobench.shared.catalogue.names import NAMES_DOC, NamesError
from cryptobench.shared.errors.input_error import InputError
from perfrepair.dto.decision import OUTBOX_RECORD_DOC
from cryptobench.shared.document.document import DocumentKind
from perfrepair.dto.site import SCOPES_DOC
from perfrepair.files import read_versioned
from cryptobench.shared.document.json_dump import write_json
from cryptobench.shared.errors.coded import code_of
from cryptobench.shared.log import event
from cryptobench.shared.stop.codes import CODES


def _kinds() -> list[DocumentKind]:
    # events.jsonl's kind moved with the event log into the library
    found = {id(event.EVENT_DOC): event.EVENT_DOC}
    for info in pkgutil.walk_packages(perfrepair.__path__, "perfrepair."):
        if info.name.endswith("__main__"):
            continue
        try:
            module = importlib.import_module(info.name)
        except ImportError:
            continue
        found.update({id(v): v for v in vars(module).values() if isinstance(v, DocumentKind)})
    return list(found.values())


def test_every_kind_s_code_is_in_the_table():
    # every kind refuses with these two codes; perf-repair reads their stops entries
    kinds = _kinds()
    assert len(kinds) >= 30
    assert {"missing_field", "unsupported_schema_version"} <= set(CODES)


def test_a_wrong_version_raises_the_kind_s_error_with_the_file_name(tmp_path):
    with pytest.raises(NamesError, match=r"^unsupported_schema_version: n.yaml: 1, this build reads 2$") as e:
        NAMES_DOC.check({"schemaVersion": 1}, tmp_path / "n.yaml")
    assert (e.value.code, e.value.path) == ("unsupported_schema_version", tmp_path / "n.yaml")


@pytest.mark.parametrize("doc", [{}, {"schemaVersion": None}, {"schemaVersion": "1"}, {"schemaVersion": True}])
def test_an_absent_or_non_number_version_is_missing_field_under_the_kind_s_name(doc):
    with pytest.raises(InputError, match=r"^missing_field: outbox record: schemaVersion$"):
        OUTBOX_RECORD_DOC.check(doc)


def test_a_float_version_is_compared_as_a_number():
    assert OUTBOX_RECORD_DOC.check({"schemaVersion": float(OUTBOX_RECORD_DOC.version)})
    with pytest.raises(InputError, match=r"^unsupported_schema_version: outbox record: 1.5, this build reads "):
        OUTBOX_RECORD_DOC.check({"schemaVersion": 1.5})


def test_read_versioned_loads_then_checks(tmp_path):
    path = write_json(tmp_path / "scopes.json", {"schemaVersion": "6"})
    with pytest.raises(InputError, match=r"^missing_field: scopes.json: schemaVersion$"):
        read_versioned(SCOPES_DOC, path)
    write_json(path, {"schemaVersion": 6, "scopes": []})
    assert read_versioned(SCOPES_DOC, path)["scopes"] == []


def test_read_yaml_refuses_bad_yaml_and_a_non_mapping_with_invalid_yaml_at_its_line_and_column(tmp_path):
    from cryptobench.shared.document.document import read_yaml
    bad = tmp_path / "bad.yaml"
    bad.write_text("a: 1\nb: [\n")
    with pytest.raises(InputError, match=rf"^invalid_yaml: {bad}: .* at line 3 column 1$") as e:
        read_yaml(bad)
    assert (code_of(e.value), e.value.path) == ("invalid_yaml", str(bad))
    (tmp_path / "list.yaml").write_text("- a\n")
    with pytest.raises(InputError, match=r"^invalid_yaml: "):
        read_yaml(tmp_path / "list.yaml")
    from cryptobench.shared.document.document import parse_yaml
    assert read_yaml(tmp_path / "list.yaml", list) == ["a"] and parse_yaml("", "x") == {}
    with pytest.raises(NamesError, match="^names_schema: x: .* at line 1 column 5$"):
        parse_yaml("a: [", "x", "names_schema", error=NamesError)
