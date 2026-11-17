"""Which build of the guide a device reads, and that a fallback is said once per provider."""
import sys

from cryptobench.stages.configuration import guide
from cryptobench.shared.device.capture import platform  # noqa: E402
from cryptobench.shared.catalogue.provider_builds import provider_builds  # noqa: E402


def test_a_device_names_its_platform_and_a_host_its_jdk():
    assert platform({"sdkInt": 37, "javaVersion": "0"}) == "android-37"
    assert platform({"javaVersion": "25.0.1"}) == "jdk-25"
    assert platform({}) is None


def test_an_exact_build_wins_and_a_newer_device_takes_the_nearest_below():
    builds = provider_builds()
    assert builds.nearest("AndroidOpenSSL", "android-33", None) == ("AndroidOpenSSL @ android-33", True)
    assert builds.nearest("AndroidOpenSSL", "android-37", None) == ("AndroidOpenSSL @ android-36", False)
    assert builds.nearest("NoSuchProvider", "android-37", None) == (None, False)


def test_a_fallback_is_one_line_per_provider():
    item = {"build": "P @ android-36", "exactBuild": False}
    lines = guide.fallbacks({"items": {"P": {"Cipher": {"A": item, "B": item}}, "Q": {"Mac": {"M": {"build": "Q @ android-37", "exactBuild": True}}}}})
    assert lines == ["guide_build_fallback: P has no row of its own for this build; using P @ android-36"]


def test_a_key_inside_its_provider_is_made_from_the_catalogues_keystore_block_else_refused():
    from cryptobench.shared.catalogue.guide_items import guide_items
    effective = {"providers": {"AndroidKeyStore": {"KeyGenerator": {"AES": {}, "HmacSHA256": {}}, "KeyPairGenerator": {"EC@sb": {}}},
                               "BC": {"KeyGenerator": {"AES": {}}}}}
    items = guide_items(effective, "android-36")["items"]
    assert items["AndroidKeyStore"]["KeyGenerator"]["AES"]["keystore"] == {
        "purposes": ["ENCRYPT", "DECRYPT"], "blockModes": ["GCM", "CBC", "CTR"], "encryptionPaddings": ["NoPadding", "PKCS7Padding"]}
    assert items["AndroidKeyStore"]["KeyPairGenerator"]["EC"]["keystore"] == {"purposes": ["SIGN", "VERIFY"], "digests": ["SHA-256"]}
    assert items["AndroidKeyStore"]["KeyGenerator"]["HmacSHA256"]["refused"].startswith("key_inside_provider:")
    assert "keystore" not in items["BC"]["KeyGenerator"]["AES"]
