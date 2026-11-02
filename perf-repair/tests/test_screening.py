import pytest
import yaml

from perfrepair.catalog.names import Names
from perfrepair.catalog.screening import SCREENING, Screening, ScreeningError

NAMES = Names.load()
SOURCES = {"S": "https://example.org/s"}


def load(tmp_path, **sections):
    doc = {"schemaVersion": 1, "sources": SOURCES, **sections}
    path = tmp_path / "screening.yaml"
    path.write_text(yaml.safe_dump(doc))
    return Screening.load(path, NAMES)


def row(status="deprecated", source="S"):
    return {"status": status, "reason": "r", "source": source}


def test_the_shipped_screening_loads_with_every_key_canonical():
    screening = Screening.load(SCREENING, NAMES)
    assert screening.crypto[("MessageDigest", "SHA-1")].status == "deprecated"
    assert screening.crypto[("Signature", "SHA256WITHRSA")].status == "accepted"
    assert screening.crypto[("Cipher", "AES/CBC/PKCS5PADDING")].status == "accepted"
    assert screening.crypto[("Mac", "SSLMACMD5")].source == "unsourced"
    assert screening.platform[("BC", "KeyFactory", "RSA")].removedApi is None


def test_a_rule_resolves_its_source_key_to_the_url(tmp_path):
    assert load(tmp_path, crypto={"MessageDigest": {"MD5": row()}}).crypto[("MessageDigest", "MD5")].source == SOURCES["S"]


@pytest.mark.parametrize("name, said", [("SHA1", "canonical is SHA-1"), ("sha-1", "canonical is SHA-1"),
                                        ("NOPE", "not in algorithm-names.yaml")])
def test_a_non_canonical_key_is_refused(tmp_path, name, said):
    with pytest.raises(ScreeningError, match=f"screening_key_not_canonical: crypto MessageDigest {name}: {said}"):
        load(tmp_path, crypto={"MessageDigest": {name: row()}})


def test_a_sized_spelling_is_not_a_key(tmp_path):
    with pytest.raises(ScreeningError, match="canonical is AES"):
        load(tmp_path, crypto={"Cipher": {"AES_128": row()}})


def test_every_problem_is_reported_at_once(tmp_path):
    with pytest.raises(ScreeningError) as e:
        load(tmp_path, crypto={"MessageDigest": {"MD5": row(status="weak"), "SHA-256": row(source="NOWHERE")}})
    assert "screening_status" in str(e.value) and "screening_source" in str(e.value)


def test_another_schema_version_is_refused(tmp_path):
    path = tmp_path / "s.yaml"
    path.write_text("schemaVersion: 2\n")
    with pytest.raises(ScreeningError, match="screening_schema"):
        Screening.load(path, NAMES)


def test_a_component_only_deprecates_and_names_catalog_modes(tmp_path):
    with pytest.raises(ScreeningError) as e:
        load(tmp_path, components={"Cipher": {"base": {"DES": row(status="accepted")}, "mode": {"XYZ": row()}}})
    assert "screening_component_status" in str(e.value) and "components mode Cipher XYZ" in str(e.value)


def test_an_accepted_row_a_component_deprecates_is_a_contradiction(tmp_path):
    with pytest.raises(ScreeningError, match="screening_contradiction: crypto Cipher AES/ECB/NOPADDING"):
        load(tmp_path, crypto={"Cipher": {"AES/ECB/NoPadding": row(status="accepted")}},
             components={"Cipher": {"mode": {"ECB": row()}}})


def platform(**over):
    return {"provider": "P", "deprecatedApi": 28, "removedApi": 31, "gate": "targetSdk", "reason": "r", "source": "S",
            "names": {"MessageDigest": ["MD5"]}, **over}


def test_a_platform_rule_needs_a_known_gate_and_ordered_api_levels(tmp_path):
    with pytest.raises(ScreeningError) as e:
        load(tmp_path, platform=[platform(gate="minSdk", removedApi=20)])
    assert "screening_gate" in str(e.value) and "screening_platform" in str(e.value)


def test_a_name_listed_by_two_platform_rules_is_a_duplicate(tmp_path):
    with pytest.raises(ScreeningError, match="screening_duplicate"):
        load(tmp_path, platform=[platform(), platform(removedApi=None)])


def test_platform_names_must_be_canonical(tmp_path):
    with pytest.raises(ScreeningError, match="screening_key_not_canonical: platform\\[0\\] P MessageDigest SHA1"):
        load(tmp_path, platform=[platform(names={"MessageDigest": ["SHA1"]})])
