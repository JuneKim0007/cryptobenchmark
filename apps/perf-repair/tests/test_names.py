from pathlib import Path

import pytest
import yaml

from cryptobench.shared.catalogue.names import CATALOG, Canonical, Names, NamesError
from perfrepair.data_handler.inbound.probe import Probe

CASES = Path(__file__).resolve().parents[2] / "benchmark/modules/config/src/test/resources/algorithm-names-cases.yaml"


@pytest.fixture(scope="module")
def names():
    return Names.load()


@pytest.mark.parametrize("case", yaml.safe_load(CASES.read_text())["cases"], ids=lambda c: f"{c['type']}:{c['name']}")
def test_the_shared_cases_resolve(names, case):
    assert names.canonical(case["type"], case["name"]) == Canonical(case["canonical"], case["keySize"], case["known"])


def test_every_catalogued_spelling_resolves_to_its_canonical_name(names):
    doc = yaml.safe_load(CATALOG.read_text())
    for engine_type, spellings in doc["names"].items():
        for canonical, aliases in spellings.items():
            for spelling in [canonical, *aliases, canonical.lower()]:
                assert names.canonical(engine_type, spelling) == Canonical(canonical), (engine_type, spelling)


def test_a_spelling_under_two_canonical_names_is_refused(tmp_path):
    path = tmp_path / "names.yaml"
    path.write_text("schemaVersion: 1\nnames:\n  MessageDigest:\n    SHA-1: [SHA]\n    SHA-0: [sha]\n")
    with pytest.raises(NamesError, match="names_catalog_duplicate"):
        Names.load(path)


@pytest.mark.parametrize("body,code", [
    ("names:\n  Cipher:\n    AES: [AES_128]\nsized:\n  Cipher:\n    AES_128: {name: AES, keySize: 128}\n", "names_catalog_duplicate: Cipher AES_128 is sized and named"),
    ("names:\n  KeyPairGenerator:\n    XDH: [1.3.101.110]\n    X25519: [OID.1.3.101.110]\n", "names_oid_split: KeyPairGenerator OID.1.3.101.110"),
])
def test_a_spelling_sized_and_named_or_an_oid_apart_from_its_bare_form_is_refused(tmp_path, body, code):
    path = tmp_path / "names.yaml"
    path.write_text("schemaVersion: 1\n" + body)
    with pytest.raises(NamesError, match=code):
        Names.load(path)


def test_a_key_algorithm_spelling_names_its_key_type_and_a_curve_family_stays_apart(tmp_path):
    names = Names.load()
    assert [names.key_type(s) for s in ("ecdsa", "DiffieHellman", "X25519", "XDH", "HmacSHA256", "ChaCha7539", "ChaCha")] == [
        Canonical("EC"), Canonical("DH"), Canonical("X25519"), Canonical("XDH", None, False), Canonical("HMAC"),
        Canonical("ChaCha20"), Canonical("CHACHA")]
    path = tmp_path / "names.yaml"
    path.write_text("schemaVersion: 1\nnames: {}\nkeyTypes:\n  EC: [ECDSA]\n  ECDSA: []\n")
    with pytest.raises(NamesError, match="names_catalog_duplicate"):
        Names.load(path)


def _probe(*services):
    return Probe({"providers": [{"name": p, "services": [{"type": t, "algorithm": a, "aliases": al}]}
                                              for p, t, a, al in services]})


def test_probe_aliases_add_names_the_catalog_lacks(names):
    merged = _probe(("P", "Cipher", "AES/GCM/NoPadding", ["VENDORGCM"])).names(names)
    assert names.canonical("Cipher", "vendorgcm") == Canonical("vendorgcm", None, False)
    assert merged.canonical("Cipher", "vendorgcm") == Canonical("AES/GCM/NoPadding")


def test_key_formats_resolve_case_insensitively(names):
    assert names.key_format("pkcs#8") == Canonical("PKCS#8")
    assert not names.key_format("PEM").known
