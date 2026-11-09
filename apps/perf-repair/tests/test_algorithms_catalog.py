import copy
import json
import shutil
from pathlib import Path

import pytest
import yaml

from cryptobench.catalogue.algorithms import DIRECTORY, AlgorithmsError, algorithms, load
from cryptobench.catalogue.families import Families
from cryptobench.catalogue.names import fold
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
    assert [i for i in items if types().of(i["family"], i["canonical"]) is None] == []


def test_a_type_fact_builds_disagree_on_holds_only_when_it_holds_on_every_build():
    undecided = sorted((e.type, e.canonical) for e in algorithms().entries if "deterministic" not in e.raw["conditions"])
    assert undecided == [("Cipher", "PBEWithSHA1AndRC4_128"), ("Cipher", "PBEWithSHA1AndRC4_40"), ("Cipher", "RSA")]
    rsa = algorithms().of("cipher.pair", "Cipher|RSA").raw["providers"]
    assert rsa["SunJCE @ jdk-25"]["conditions.deterministic"]["value"] == "never"
    assert rsa["BC @ jdk-25"]["conditions.deterministic"]["value"] == "always"
    assert types().of("cipher.pair", "RSA").properties.deterministic is False


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


def test_an_entry_now_states_its_type_facts_with_its_contract():
    entry = algorithms().of("cipher.secret", "Cipher|PBEWithHmacSHA1AndAES_128")
    assert entry.contract and types().of("cipher.secret", "PBEWithHmacSHA1AndAES_128").properties.parameters == "pbe"
    assert [e.id for e in algorithms().entries if e.sourced("strengthBits") is None] == []


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
    ("digest.none_catalogue.yaml", _md5(lambda e: e["required"].append({"name": "iv", "rule": "sometimes", "source": "inferred"})), "nonce rule"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", source="NOWHERE"), "source 'NOWHERE'"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", source="unsourced"), "source 'unsourced'"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", source="sourced", url=None), "no url"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["conditions"]["deterministic"].update(value=True)), "deterministic"),
    ("digest.none_catalogue.yaml", _fact("minSdk", value=0), "minSdk"),
    ("digest.none_catalogue.yaml", _fact("minSdk", value=True), "minSdk"),
    ("digest.none_catalogue.yaml", _fact("minSdk", source="unsourced"), "source 'unsourced'"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.update(colour="red")), "unknown \\['colour'\\]"),
    # spellings live only in algorithm-names.yaml
    ("digest.none_catalogue.yaml", _md5(lambda e: e.update(aliases=["MD-5"])), "unknown \\['aliases'\\]"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.pop("providers")), "missing \\['providers'\\]"),
    ("digest.none_catalogue.yaml", _fact("strengthBits", value={"key": "rot13"}), "keyStrength map"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["sourcedOnly"].pop()), "type facts missing"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e.update(contract={"output": {}})), "contract"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"].pop("key")), "is not \\{key, input, output\\}"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"].update(key="keystore")), "contract key 'keystore'"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["contract"]["output"].update(function={"value": "MD5", "assumed": False})),
     "contract output is not a mapping"),
    ("digest.none_catalogue.yaml", _md5(lambda e: e["key"].update(source="hearsay")), "hearsay"),
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


def _leaves(raw):
    yield from [raw["key"], *raw["required"], *raw["optional"], *raw["conditions"].values(), *raw["sourcedOnly"]]


def test_every_cited_url_is_listed_and_a_null_fact_is_never_sourced():
    catalogue = algorithms()
    listed = set(catalogue.common.sources.values())
    for e in catalogue.entries:
        for leaf in _leaves(e.raw):
            if leaf["source"] == "sourced":
                assert leaf["url"] in listed, e.id
        assert not [s for s in e.raw["sourcedOnly"] if s["value"] is None and s["source"] == "sourced"], e.id


@pytest.mark.parametrize("field", ["passwordBased", "wrap", "prehashed"])
@pytest.mark.parametrize("value", [1, 0, "TRUE"])
def test_a_contract_boolean_refuses_anything_but_a_boolean(tmp_path, field, value):
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    path = target / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"]["Cipher|AES/GCM/NoPadding"]["contract"]["input"][field] = value
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="is not a boolean"):
        load(target)


@pytest.mark.parametrize("identifier,facts", [
    ("KeyGenerator|AES", {"required": []}),
    ("KeyPairGenerator|ELGAMAL", {"required": []}),
    ("Cipher|ECIES", {"authenticated": True}),
    ("Cipher|SM2", {"authenticated": True}),
    ("Signature|NONEwithECDSAinP1363Format", {"authenticated": True}),
    ("Cipher|AES/GCM-SIV/NoPadding", {"key": [16, 32]})])
def test_the_facts_the_reviews_found_contradicted_hold_the_observed_value(identifier, facts):
    family = next(e.family for e in algorithms().entries if e.id == identifier)
    raw = algorithms().of(family, identifier).raw
    if "required" in facts:
        assert raw["required"] == []
    if "authenticated" in facts:
        assert raw["conditions"]["authenticated"] == {"value": True, "source": "measured"}
    if "key" in facts:
        assert raw["key"]["bytes"] == facts["key"]


def test_pkcs1_input_is_limited_by_the_key_size():
    assert algorithms().of("cipher.pair", "Cipher|RSA/ECB/PKCS1Padding").raw["conditions"]["input"] == {"value": "maxBytes", "bytes": 245, "source": "measured"}


def test_a_post_quantum_base_is_the_standard_s_default_and_a_build_s_output_its_difference():
    raw = algorithms().of("signature.pair", "Signature|ML-DSA-65").raw
    assert raw["conditions"]["deterministic"]["source"] == "sourced" and "FIPS.204" in raw["conditions"]["deterministic"]["url"]
    assert raw["conditions"]["deterministic"]["value"] == "never"
    assert raw["providers"]["BundledBC @ org.bouncycastle:bcprov-jdk18on:1.79"]["conditions.deterministic"] == {"value": "always", "source": "measured"}


def test_nonce_reuse_is_what_an_app_sees_per_build_and_no_base_holds_it_when_builds_disagree():
    raw = algorithms().of("cipher.secret", "Cipher|AES/GCM/NoPadding").raw
    assert "reuseRefused" not in raw["conditions"]
    assert raw["providers"]["SunJCE @ jdk-25"]["conditions.reuseRefused"]["value"] is True
    assert raw["providers"]["BundledBC @ org.bouncycastle:bcprov-jdk18on:1.79"]["conditions.reuseRefused"]["value"] is False


def test_a_base_value_holds_for_every_build_that_observed_it():
    raw = algorithms().of("cipher.secret", "Cipher|AES/GCM/NoPadding").raw
    assert "bytes" not in raw["key"]
    assert raw["providers"]["BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"]["key.bytes"] == [16, 32]
    assert raw["providers"]["BC @ jdk-25"]["key.bytes"] == [16, 24, 32]


ABSENT = object()


def value_at(entry: dict, path: str):
    """The value at an override path: required.<name> or optional.<name> is the row of that name, ABSENT when none holds it."""
    steps = path.split(".")
    node = entry
    if steps[0] in ("required", "optional"):
        node = next((r for r in entry.get(steps[0]) or [] if r.get("name") == steps[1]), None)
        steps = steps[2:]
        if node is None:
            return None if not steps else ABSENT
    for step in steps:
        if not isinstance(node, dict) or step not in node:
            return ABSENT
        node = node[step]
    return node


def test_a_base_and_a_build_differ_only_where_a_kept_fix_says_so_never_by_count():
    differing = set()
    for e in algorithms().entries:
        base = {k: v for k, v in e.raw.items() if k != "providers"}
        for build, over in e.raw["providers"].items():
            for path in over:
                if value_at(base, path) not in (ABSENT, None):
                    keystore = build.startswith("AndroidKeyStore") and path in ("key.origin", "contract.key")
                    standard = path == "conditions.deterministic" and e.raw["conditions"]["deterministic"]["source"] == "sourced"
                    password_alias = e.canonical.startswith("PBEWithHmac") and ("AndroidOpenSSL" in build or "BundledConscrypt" in build)
                    reset = path.startswith("lifecycle.reset.") and over[path]["source"] == "measured"
                    if not (keystore or standard or password_alias or reset):
                        differing.add((e.id, build, path))
    assert differing == set()


def test_a_type_row_reads_a_parameter_object_only_builds_carry():
    assert types().of("cipher.secret", "PBEWithMD5AndDES").properties.parameters == "pbe"
    chacha = types().of("cipher.secret", "ChaCha20").properties
    assert (chacha.parameters, chacha.nonceRequired) == ("iv", "unique")


def test_a_spelling_that_is_another_service_is_measured_only_where_it_ran():
    providers = algorithms().of("cipher.pair", "Cipher|RSA/ECB/OAEPWithSHA-224AndMGF1Padding").raw["providers"]
    sources = {a: providers[f"AndroidKeyStoreBCWorkaround @ android-{a}"]["conditions.spellingRuns"]["source"] for a in (26, 30, 33, 36)}
    assert sources == {26: "inferred", 30: "inferred", 33: "measured", 36: "measured"}


def test_the_conscrypt_password_refusal_is_measured_on_the_alias():
    over = algorithms().of("cipher.secret", "Cipher|PBEWithHmacSHA256AndAES_128").raw["providers"]["BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"]
    assert over["required.password"] is None and over["required.secretKey"]["source"] == "measured"


def test_the_keystore_born_pairs_are_keyed_by_build():
    gcm = algorithms().of("cipher.secret", "Cipher|AES/GCM/NoPadding").raw["providers"]
    assert all(gcm[f"AndroidKeyStoreBCWorkaround @ android-{a}"]["contract.key"] == "provider" for a in (26, 30, 33, 36))
    oaep = algorithms().of("cipher.pair", "Cipher|RSA/ECB/OAEPWithSHA-256AndMGF1Padding").raw["providers"]
    assert oaep["AndroidKeyStoreBCWorkaround @ android-26"]["key.origin"] == "provider"
    # an app key "works" here only because the provider hands it to a software cipher; the key it can use itself stays inside
    assert oaep["AndroidKeyStoreBCWorkaround @ android-33"]["key.origin"] == "provider"


def test_a_password_cipher_with_an_iv_takes_one_object_holding_the_iv():
    from cryptobench.catalogue.recipes import recipes
    entries = [e for e in algorithms().entries if e.required("salt") and e.required("iv")]
    assert len(entries) == 14
    for e in entries:
        assert {e.required(n)["recipe"] for n in ("salt", "iterationCount", "iv")} == {"jca.pbeIvSpec"}, e.id
    assert recipes().roles("jca.pbeIvSpec") == {"salt", "iterationCount", "iv"}
    assert types().of("cipher.secret", "PBEWithHmacSHA256AndAES_256").properties.parameters == "pbe"


def test_a_build_s_own_iv_stays_its_own_object():
    over = algorithms().of("cipher.secret", "Cipher|PBEWithHmacSHA256AndAES_128").raw["providers"]["BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"]
    assert over["required.iv"]["recipe"] == "jca.ivSpec"


def test_two_objects_for_one_call_are_refused():
    from cryptobench.catalogue.algorithms import Entry, entry_problems
    from cryptobench.catalogue.recipes import recipes
    catalogue = algorithms()
    raw = copy.deepcopy(catalogue.of("cipher.secret", "Cipher|PBEWithHmacSHA256AndAES_256").raw)
    next(r for r in raw["required"] if r["name"] == "iv")["recipe"] = "jca.ivSpec"
    found = entry_problems(Entry("Cipher|PBEWithHmacSHA256AndAES_256", "cipher.secret", raw), catalogue.common, None, recipes())
    assert any("init takes one object" in p for p in found)


def test_one_object_split_across_two_calls_is_refused():
    from cryptobench.catalogue.algorithms import Entry, entry_problems
    from cryptobench.catalogue.recipes import recipes
    catalogue, ident = algorithms(), "Cipher|PBEWithSHA1AndRC4_128"
    raw = copy.deepcopy(catalogue.of("cipher.secret", ident).raw)
    assert {r["passedTo"] for r in raw["required"] if r.get("recipe") == "jca.pbeKeySpecDerived"} == {"generateSecret"}
    next(r for r in raw["required"] if r["name"] == "salt")["passedTo"] = "init"
    found = entry_problems(Entry(ident, "cipher.secret", raw), catalogue.common, None, recipes())
    assert "recipe jca.pbeKeySpecDerived is one object, the rows pass it to ['generateSecret', 'init']" in found


NO_RESET_CIPHERS = ("Cipher|AES/GCM/NoPadding", "Cipher|ARIA/GCM/NoPadding", "Cipher|ChaCha20-Poly1305")


def test_a_nonce_aead_encrypt_needs_a_new_init_where_its_decrypt_does_not():
    for ident in NO_RESET_CIPHERS:
        reset = algorithms().of("cipher.secret", ident).raw["lifecycle"]["reset"]
        assert reset == {"forward": {"value": "none", "source": "measured"}, "reverse": {"value": "afterInit", "source": "measured"}}, ident


def test_only_the_gmacs_a_run_refused_lose_their_reset():
    none = {e.id for e in algorithms().family("mac.secret") if e.raw["lifecycle"]["reset"]["forward"]["value"] == "none"}
    assert len(none) == 11 and all(i.endswith("-GMAC") for i in none)
    assert not any("DSTU7624" in i for i in none)


def test_ccm_and_gcm_siv_reset_except_where_conscrypt_refuses_a_second_gcm_siv_encrypt():
    for ident in ("Cipher|AES/CCM/NoPadding", "Cipher|AES/GCM-SIV/NoPadding", "Cipher|ARIA/CCM/NoPadding"):
        assert algorithms().of("cipher.secret", ident).raw["lifecycle"]["reset"]["forward"]["value"] == "afterInit", ident
    siv = algorithms().of("cipher.secret", "Cipher|AES/GCM-SIV/NoPadding").raw["providers"]
    refusing = {b for b, o in siv.items() if o.get("lifecycle.reset.forward", {}).get("value") == "none"}
    assert refusing == {"AndroidOpenSSL @ android-30", "AndroidOpenSSL @ android-33", "AndroidOpenSSL @ android-36", "BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"}


def test_reset_holds_the_directions_of_the_operations_and_a_digest_reset_is_measured():
    from cryptobench.catalogue.glossary import directions_of
    for e in algorithms().entries:
        assert set(e.raw["lifecycle"]["reset"]) == directions_of(e.raw["operations"]["value"]), e.id
    digest = algorithms().of("digest.none", "MessageDigest|SHA-256").raw["lifecycle"]["reset"]
    assert set(digest) == {"forward"} and digest["forward"]["source"] == "measured"
    assert set(algorithms().of("signature.pair", "Signature|HSS/LMS").raw["lifecycle"]["reset"]) == {"reverse"}


def test_a_parameter_object_no_run_built_is_inferred():
    assert algorithms().of("cipher.secret", "Cipher|RC5-64").required("providerSpec")["source"] == "inferred"
    kem = [e for e in algorithms().family("keygen.none") if e.required("publicKey")]
    assert len(kem) == 5 and {e.required("publicKey")["source"] for e in kem} == {"inferred"}


def test_a_standard_is_cited_only_for_its_own_names_and_only_where_a_build_shows_it():
    cited = {e.id: e.raw["conditions"]["deterministic"] for e in algorithms().family("signature.pair") if e.raw["conditions"]["deterministic"]["source"] == "sourced"}
    assert sorted(cited) == ["Signature|ML-DSA", "Signature|ML-DSA-44", "Signature|ML-DSA-65", "Signature|ML-DSA-87", "Signature|SLH-DSA-SHA2-128S"]
    for ident in ("Signature|MLDSA44-Ed25519-SHA512", "Signature|SPHINCSPLUS", "Signature|HASH-ML-DSA"):
        raw = algorithms().of("signature.pair", ident).raw
        assert (raw["conditions"]["deterministic"]["source"], raw["conditions"]["deterministic"]["value"]) == ("measured", "always"), ident
