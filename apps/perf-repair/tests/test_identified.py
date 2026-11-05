"""The one identified test's alias policy: a device alias the catalog names otherwise is reported and never followed."""
import pytest
from perfrepair.catalog.names import Names, NamesError
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.probe.identified import alias_conflicts

PBE = "PBEWithHmacSHA1AndAES_128"
PROBE = Probe({"providers": [{"name": "P1", "services": [
    {"type": "Cipher", "algorithm": "AES/CBC/PKCS5Padding", "aliases": [PBE, "AESCBCNEW"], "attributes": {}}]}]})


def test_a_device_alias_the_catalog_names_otherwise_is_reported_and_not_followed():
    names = PROBE.names(Names.load())
    assert alias_conflicts(names) == [(f"Cipher|{PBE.upper()}", f"catalog says {PBE}; P1 says AES/CBC/PKCS5Padding")]
    with pytest.raises(NamesError, match="name_conflict"):
        names.canonical("Cipher", PBE)
    assert names.canonical("Cipher", "AESCBCNEW").name == "AES/CBC/PKCS5Padding"


def test_no_probe_no_conflict():
    assert alias_conflicts(Names.load()) == []
