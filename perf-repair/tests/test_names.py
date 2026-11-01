from pathlib import Path

import pytest
import yaml

from perfrepair.catalog.names import CATALOG, Canonical, Names, NamesError
from perfrepair.catalog.probe_names import with_probe

CASES = Path(__file__).parent / "fixtures" / "algorithm-names-cases.yaml"


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


def _probe(*services):
    return {"providers": [{"name": p, "services": [{"type": t, "algorithm": a, "aliases": al}]}
                          for p, t, a, al in services]}


def test_probe_aliases_add_names_the_catalog_lacks(names):
    merged = with_probe(names, _probe(("P", "Cipher", "AES/GCM/NoPadding", ["GCM"])))
    assert names.canonical("Cipher", "gcm") == Canonical("gcm", None, False)
    assert merged.canonical("Cipher", "gcm") == Canonical("AES/GCM/NoPadding")


def test_a_probe_alias_the_catalog_disagrees_with_is_a_coded_error_where_used(names):
    merged = with_probe(names, _probe(("P", "Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding",
                                       ["RSA/None/OAEPWithSHA-224AndMGF1Padding"])))
    assert merged.canonical("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding").known
    with pytest.raises(NamesError, match="name_conflict: Cipher RSA/None/OAEPWithSHA-224AndMGF1Padding: catalog says"):
        merged.canonical("Cipher", "RSA/None/OAEPWithSHA-224AndMGF1Padding")


def test_two_providers_that_alias_one_spelling_apart_conflict(names):
    merged = with_probe(names, _probe(("P", "KeyStore", "Foo", ["Bar"]), ("Q", "KeyStore", "Baz", ["bar"])))
    with pytest.raises(NamesError, match="P says Foo, Q says Baz"):
        merged.canonical("KeyStore", "BAR")


def test_key_formats_resolve_case_insensitively(names):
    assert names.key_format("pkcs#8") == Canonical("PKCS#8")
    assert not names.key_format("PEM").known
