import pytest

from cryptobench.shared.device import aliases
from cryptobench.shared.errors.input_error import InputError


def written(tmp_path, text):
    path = tmp_path / "devices.yaml"
    path.write_text(text)
    return path


def test_no_file_is_no_aliases(tmp_path):
    assert aliases.read(tmp_path / "devices.yaml") == {}


def test_aliases_name_keys(tmp_path):
    path = written(tmp_path, "schemaVersion: 1\naliases: {pixel10: 56301AAAA00001, api33: 'emulator:cb-api33'}\n")
    assert aliases.read(path) == {"pixel10": "56301AAAA00001", "api33": "emulator:cb-api33"}


@pytest.mark.parametrize("text, code", [
    ("schemaVersion: 1\naliases: [a]\n", "invalid_alias"),
    ("schemaVersion: 1\naliases: {'a:b': X}\n", "invalid_alias"),
    ("schemaVersion: 1\naliases: {a: ''}\n", "invalid_alias"),
    ("schemaVersion: 1\naliases: {a: X, b: X}\n", "duplicate_alias"),
    ("schemaVersion: 1\nalias: {a: X}\n", "unknown_keys"),
    ("schemaVersion: 1\naliases: {a: [\n", "invalid_yaml"),
])
def test_a_bad_file_is_refused_with_its_code(tmp_path, text, code):
    with pytest.raises(InputError) as refused:
        aliases.read(written(tmp_path, text))
    assert refused.value.code == code


def test_another_schema_version_is_refused_by_the_document_check(tmp_path):
    with pytest.raises(InputError, match="unsupported_schema_version: devices.yaml: 2, this build reads 1"):
        aliases.read(written(tmp_path, "schemaVersion: 2\naliases: {}\n"))
