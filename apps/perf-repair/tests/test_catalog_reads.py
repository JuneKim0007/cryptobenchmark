import pytest

from perfrepair.catalog.sdk_constants import sdk_constants
from perfrepair.catalog.upgrades import Upgrades
from cryptobench.shared.errors.input_error import InputError


# Catalogue files read through DocumentKind.read: bad YAML is a coded input error, not a raw parser error.
@pytest.mark.parametrize("read", [sdk_constants.__wrapped__, Upgrades.load])
def test_bad_yaml_in_a_catalogue_is_an_input_error(tmp_path, read):
    path = tmp_path / "broken.yaml"
    path.write_text("schemaVersion: 1\nconstants: [\n")
    with pytest.raises(InputError):
        read(path)


@pytest.mark.parametrize("read", [sdk_constants.__wrapped__, Upgrades.load])
def test_another_schema_version_is_refused(tmp_path, read):
    path = tmp_path / "future.yaml"
    path.write_text("schemaVersion: 99\n")
    with pytest.raises(InputError, match="^unsupported_schema_version: future.yaml: 99, this build reads 1$"):
        read(path)
