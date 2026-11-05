import json
import shutil
from pathlib import Path

import pytest
import yaml

from perfrepair.catalog.algorithms import DIRECTORY, AlgorithmsError, algorithms, load
from perfrepair.catalog.families import Families
from perfrepair.catalog.names import fold
from perfrepair.catalog.screening import SCREENING
from perfrepair.catalog.types import types

FIXTURE = Path(__file__).parent / "fixtures" / "types" / "pixel-10-items.json"
MD5 = "MessageDigest|MD5"


def _family_types() -> dict[str, str]:
    return {f.id: f.type for f in Families.load().all}


def test_every_family_has_a_catalogue_and_every_entry_its_family_s_engine_type():
    catalogue, engine = algorithms(), _family_types()
    assert {e.family for e in catalogue.entries} == set(engine)
    assert [e.id for e in catalogue.entries if e.type != engine[e.family]] == []


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
    # the device's evidence puts DESedeWrap in cipher.unknown; the catalogue holds it in cipher.secret only
    assert [i for i in items if types().of(i["family"], i["canonical"]) is None] == [
        {"type": "Cipher", "family": "cipher.unknown", "canonical": "DESedeWrap"}]


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


def test_an_entry_without_type_facts_has_a_contract_but_no_type():
    entry = algorithms().of("cipher.unknown", "Cipher|PBEWithHmacSHA1AndAES_128")
    assert entry.contract and types().of("cipher.unknown", "PBEWithHmacSHA1AndAES_128") is None


def _copy(tmp_path, file: str, mutate) -> Path:
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    path = target / file
    doc = yaml.safe_load(path.read_text())
    mutate(doc)
    path.write_text(yaml.safe_dump(doc))
    return target


def _md5(change):
    return lambda d: change(d["algorithms"][MD5])


def _fact(name: str, **values):
    return _md5(lambda e: next(f for f in e["sourcedOnly"] if f["fact"] == name).update(values))


@pytest.mark.parametrize("file,mutate,code", [
    ("digest.none_catalogue.yaml", _md5(lambda e: e["conditions"]["output"].update(kind="hash")), "output kind"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["required"][1].update(value="sometimes")), "nonce"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", source="NOWHERE"), "not a listed source"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", source="unsourced"), "unsourced strength"),
    ("digest.none_catalogue.yaml", _fact("minSdk", value=0), "minSdk"),
    ("digest.none_catalogue.yaml", _fact("minSdk", value=True), "minSdk"),
    ("digest.none_catalogue.yaml", _fact("minSdk", source="unsourced"), "not a listed source"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.update(colour="red")), "unknown \\['colour'\\]"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.pop("providers")), "missing \\['providers'\\]"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", value={"key": "rot13"}), "keyStrength map"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["sourcedOnly"].pop()), "type facts missing"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.update(contract={"output": {}})), "contract"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"].pop("key")), "is not \\{key, input, output\\}"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"].update(key="keystore")), "contract key 'keystore'"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"]["output"].update(function={"value": "MD5", "assumed": False})),
     "contract output is not a mapping"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["key"].update(source="hearsay")), "hearsay"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["provenance"].update(by="nobody")), "provenance"),
    ("digest.none_catalogue.yaml", lambda d: d["algorithms"].update({"MD4": d["algorithms"][MD5]}), "is not <type>"),
    ("digest.none_catalogue.yaml", lambda d: d.update(family="mac.secret"), "family"),
    ("common.yaml", lambda d: d.update(deterministicRelied=["noise"]), "deterministicRelied"),
])
def test_a_bad_entry_is_refused_with_its_reason(tmp_path, file, mutate, code):
    with pytest.raises(AlgorithmsError, match=code):
        load(_copy(tmp_path, file, mutate))


def test_a_stray_catalogue_a_missing_one_and_an_old_schema_are_refused(tmp_path):
    target = _copy(tmp_path, "common.yaml", lambda d: None)
    (target / "digest.none_catalogue.yaml").rename(target / "digest.other_catalogue.yaml")
    with pytest.raises(AlgorithmsError, match="digest.other_catalogue.yaml: not a family.*no digest.none_catalogue.yaml"):
        load(target)
    with pytest.raises(AlgorithmsError, match="algorithms_invalid: .*schemaVersion 0 is not 1"):
        load(_copy(tmp_path / "v", "common.yaml", lambda d: d.update(schemaVersion=0)))
