"""dto/document.py and dto/coded.py: the one schemaVersion check, its error type, its reader's own wording."""
import importlib
import pkgutil

import pytest

import perfrepair
from cryptobench.catalogue.names import NAMES_DOC, NamesError
from cryptobench.catalogue.coded import InputError
from perfrepair.dto.decision import OUTBOX_RECORD_DOC
from cryptobench.catalogue.document import DocumentKind
from perfrepair.dto.site import SCOPES_DOC
from perfrepair.files import read_versioned, write_json
from perfrepair.stop import CODES, code_of


def _kinds() -> list[DocumentKind]:
    found = {}
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
    # the raise-site scan in test_stop sees only raise literals; a kind's code lives in its message
    kinds = _kinds()
    assert len(kinds) >= 30
    codes = {code_of(InputError(k.message.format(name=k.name, found=0, version=k.version, path="/d/f.yaml"))) for k in kinds}
    assert codes - {None} <= set(CODES)


def test_a_wrong_version_raises_the_kind_s_error_with_its_wording(tmp_path):
    with pytest.raises(NamesError) as e:
        NAMES_DOC.check({"schemaVersion": 2}, tmp_path / "n.yaml")
    assert (e.value.code, e.value.path) == ("names_schema", tmp_path / "n.yaml")


def test_an_absent_version_is_refused():
    with pytest.raises(InputError):
        OUTBOX_RECORD_DOC.check({})


def test_read_versioned_loads_then_checks(tmp_path):
    path = write_json(tmp_path / "scopes.json", {"schemaVersion": "6"})
    with pytest.raises(InputError, match=r"^schema_version: "):
        read_versioned(SCOPES_DOC, path)
    write_json(path, {"schemaVersion": 6, "scopes": []})
    assert read_versioned(SCOPES_DOC, path)["scopes"] == []


def test_read_yaml_refuses_bad_yaml_and_a_non_mapping_with_invalid_yaml_at_its_line_and_column(tmp_path):
    from perfrepair.files import read_yaml
    bad = tmp_path / "bad.yaml"
    bad.write_text("a: 1\nb: [\n")
    with pytest.raises(InputError, match=rf"^invalid_yaml: {bad}: .* at line 3 column 1$") as e:
        read_yaml(bad)
    assert (code_of(e.value), e.value.path) == ("invalid_yaml", str(bad))
    (tmp_path / "list.yaml").write_text("- a\n")
    with pytest.raises(InputError, match=r"^invalid_yaml: "):
        read_yaml(tmp_path / "list.yaml")
    from cryptobench.catalogue.document import parse_yaml
    assert read_yaml(tmp_path / "list.yaml", list) == ["a"] and parse_yaml("", "x") == {}
    with pytest.raises(NamesError, match="^names_schema: x: .* at line 1 column 5$"):
        parse_yaml("a: [", "x", "names_schema", error=NamesError)
