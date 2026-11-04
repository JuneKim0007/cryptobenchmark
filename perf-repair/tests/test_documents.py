"""dto/document.py and dto/coded.py: the one schemaVersion check, its error type, its reader's own wording."""
import importlib
import pkgutil

import pytest

import perfrepair
from perfrepair.catalog.names import NAMES_DOC, NamesError
from perfrepair.dto.coded import InputError
from perfrepair.dto.decision import OUTBOX_RECORD_DOC
from perfrepair.dto.document import DocumentKind
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
    assert str(e.value) == f"names_schema: {tmp_path / 'n.yaml'}: schemaVersion 2 is not 1"
    assert (e.value.code, e.value.path, e.value.detail) == ("names_schema", tmp_path / "n.yaml", "schemaVersion 2 is not 1")
    assert isinstance(e.value, ValueError)


def test_several_accepted_versions_and_an_absent_one():
    assert OUTBOX_RECORD_DOC.check({"schemaVersion": 1}) == {"schemaVersion": 1}
    with pytest.raises(InputError, match=r"^outbox record schemaVersion None is not one of \(1, 2\)$"):
        OUTBOX_RECORD_DOC.check({})


def test_read_versioned_loads_then_checks(tmp_path):
    path = write_json(tmp_path / "scopes.json", {"schemaVersion": "5"})
    with pytest.raises(InputError, match=r"^schema_version: .*scopes.json schemaVersion '5' is not 5; rerun"):
        read_versioned(SCOPES_DOC, path)
    write_json(path, {"schemaVersion": 5, "scopes": []})
    assert read_versioned(SCOPES_DOC, path)["scopes"] == []
