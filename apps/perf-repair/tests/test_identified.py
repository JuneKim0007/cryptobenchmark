"""The one identified test's alias policy: a device alias the catalog names otherwise is reported; the catalog's name wins."""

from perfrepair.catalog.names import Names
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.probe.identified import alias_conflicts

PBE = "PBEWithHmacSHA1AndAES_128"
PROBE = Probe({"providers": [{"name": "P1", "services": [
    {"type": "Cipher", "algorithm": "AES/CBC/PKCS5Padding", "aliases": [PBE, "AESCBCNEW"], "attributes": {}}]}]})


def test_a_device_alias_the_catalog_names_otherwise_is_reported_and_takes_the_catalog_name():
    names = PROBE.names(Names.load())
    assert alias_conflicts(names) == [(f"Cipher|{PBE.upper()}", f"catalog says {PBE}; P1 says AES/CBC/PKCS5Padding")]
    assert names.canonical("Cipher", PBE.upper()).name == PBE
    assert names.canonical("Cipher", "AESCBCNEW").name == "AES/CBC/PKCS5Padding"


def test_no_probe_no_conflict():
    assert alias_conflicts(Names.load()) == []
