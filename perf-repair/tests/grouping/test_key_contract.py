from pathlib import Path

import pytest

from perfrepair.catalog.families import Families
from perfrepair.catalog.names import Names
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN
from perfrepair.files import read_document
from perfrepair.grouping.build.items import build
from perfrepair.grouping.build.key_contract import key_contract

ROOT = Path(__file__).parents[1] / "fixtures" / "runtimes"
EXPECTED = {
    "android36": {KEY_APP_HELD: 63, KEY_PROVIDER_HELD: 38, KEY_UNKNOWN: 67},
    "jdk17": {KEY_APP_HELD: 103, KEY_PROVIDER_HELD: 0, KEY_UNKNOWN: 90},
    "jdk21": {KEY_APP_HELD: 105, KEY_PROVIDER_HELD: 0, KEY_UNKNOWN: 95},
    "jdk25": {KEY_APP_HELD: 105, KEY_PROVIDER_HELD: 0, KEY_UNKNOWN: 109},
}


def contracts(runtime):
    probe = Probe(read_document(ROOT / runtime / "probe.yaml"))
    items, profiles = build(probe, probe.names(Names.load()), read_document(ROOT / runtime / "trial.yaml"),
                            Families.load())
    return {i.qualified: profiles[i.id].keyContract for i in items}


@pytest.mark.parametrize("formats,classes,want", [
    (("RAW",), (), KEY_APP_HELD),
    (("PKCS#8", "X.509"), (), KEY_APP_HELD),
    (("RAW",), ("vendor.Handle",), KEY_APP_HELD),
    ((), ("java.security.interfaces.RSAPrivateKey",), KEY_APP_HELD),
    ((), ("javax.crypto.SecretKey",), KEY_APP_HELD),
    ((), ("vendor.RsaKey", "java.security.interfaces.RSAPrivateKey"), KEY_APP_HELD),
    ((), ("vendor.Handle",), KEY_PROVIDER_HELD),
    ((), (), KEY_UNKNOWN),
])
def test_the_rule(formats, classes, want):
    assert key_contract(formats, classes) == want


@pytest.mark.parametrize("runtime", sorted(EXPECTED))
def test_the_counts_per_runtime_are_pinned(runtime):
    seen = list(contracts(runtime).values())
    assert {c: seen.count(c) for c in EXPECTED[runtime]} == EXPECTED[runtime]


@pytest.mark.parametrize("engine,name", [
    ("Cipher", "AES/GCM/NoPadding"),
    ("Cipher", "AES/CBC/NoPadding"),
    ("Mac", "HmacSHA256"),
    ("Cipher", "RSA/ECB/OAEPWithSHA-256AndMGF1Padding"),
    ("Signature", "SHA256withRSA"),
])
def test_the_twins_on_the_device_differ(engine, name):
    seen = contracts("android36")
    assert seen[f"{engine}|{name}|AndroidOpenSSL"] == KEY_APP_HELD
    assert seen[f"{engine}|{name}|AndroidKeyStoreBCWorkaround"] == KEY_PROVIDER_HELD


def test_a_registered_key_store_is_not_evidence_and_no_attribute_is_unknown():
    seen = contracts("android36")
    assert seen["Cipher|AES|BC"] == KEY_APP_HELD
    assert seen["Cipher|DES|BC"] == KEY_UNKNOWN
    assert seen["KeyAgreement|ECDH|AndroidKeyStore"] == KEY_UNKNOWN


@pytest.mark.parametrize("runtime", ["jdk17", "jdk21", "jdk25"])
def test_no_jdk_item_is_provider_held(runtime):
    seen = contracts(runtime)
    assert KEY_PROVIDER_HELD not in seen.values()
    assert seen["Cipher|AES/GCM/NoPadding|SunJCE"] == KEY_APP_HELD
    assert seen["Signature|SHA256withRSA|SunRsaSign"] == KEY_APP_HELD
    assert seen["MessageDigest|SHA-256|SUN"] == KEY_UNKNOWN
