import json
from pathlib import Path

import pytest
import yaml

from perfrepair.catalog.families import Families
from perfrepair.catalog.names import fold
from perfrepair.catalog.screening import SCREENING
from perfrepair.catalog.types import CATALOG, TypesError, load, types

FIXTURE = Path(__file__).parent / "fixtures" / "types" / "pixel-10-items.json"


def _family_types() -> dict[str, str]:
    return {f.id: f.type for f in Families.load().all}


def test_catalog_loads_and_every_row_is_checked():
    t = types()
    assert t.rows and all(r.family in _family_types() for r in t.rows.values())


def test_every_screening_name_of_a_family_engine_has_a_type():
    by_type = {}
    for (family, name) in types().rows:
        by_type.setdefault(_family_types()[family], set()).add(name)
    crypto = yaml.safe_load(SCREENING.read_text())["crypto"]
    missing = [(engine, n) for engine, names in crypto.items() if engine in by_type
               for n in names if fold(n) not in by_type[engine]]
    assert missing == []


def test_every_device_item_with_a_canonical_name_has_a_type():
    items = json.loads(FIXTURE.read_text())["items"]
    assert [i for i in items if types().of(i["family"], i["canonical"]) is None] == []


@pytest.mark.parametrize("family,name,key,bits", [
    ("digest.none", "SHA-256", None, 128), ("digest.none", "MD5", None, 0), ("cipher.secret", "AES/CBC/PKCS5Padding", 256, 256),
    ("cipher.secret", "AES/CBC/PKCS5Padding", None, None), ("signature.pair", "SHA256withRSA", 2048, 112),
    ("signature.pair", "SHA256withRSA", 4096, 128), ("signature.pair", "SHA1withRSA", 3072, 80),
    ("cipher.pair", "RSA/ECB/OAEPPadding", 512, 0), ("signature.pair", "ML-DSA", 1, None)])
def test_strength_reads_the_key_size_table_below_it_and_caps_by_the_hash(family, name, key, bits):
    t = types()
    assert t.strength(t.of(family, name), key) == bits


def test_names_fold_and_unknown_names_have_no_type():
    t = types()
    assert t.of("digest.none", "sha-256") is t.of("digest.none", "SHA-256")
    assert t.of("digest.none", "NOPE") is None and t.of("digest.none", None) is None
    assert t.of("mac.secret", "SHA-256") is None


def _write(tmp_path, mutate) -> Path:
    doc = yaml.safe_load(CATALOG.read_text())
    mutate(doc)
    p = tmp_path / "types.yaml"
    p.write_text(yaml.safe_dump(doc))
    return p


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(outputKind="hash"), "outputKind"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(nonceRequired="sometimes"), "nonceRequired"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(strengthSource="NOWHERE"), "not a listed source"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(strengthSource="unsourced"), "unsourced strength"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(minSdk=0), "minSdk"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(colour="red"), "types_fields"),
    (lambda d: d["families"]["digest.none"]["rows"]["MD5"].update(strengthBits={"key": "rot13"}), "keyStrength map"),
    (lambda d: d["families"].update({"digest.other": d["families"]["digest.none"]}), "not a family"),
    (lambda d: d.update(deterministicRelied=["noise"]), "deterministicRelied"),
])
def test_a_bad_row_is_refused_with_its_reason(tmp_path, mutate, code):
    with pytest.raises(TypesError, match=code):
        load(_write(tmp_path, mutate))
