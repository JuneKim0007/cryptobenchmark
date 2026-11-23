"""A spelling's key type comes from its catalogue entry as every build of the provider gives it; no entry, or builds that disagree, give none."""
import yaml

from cryptobench.shared import paths
from cryptobench.shared.catalogue.algorithms import Algorithms, Entry, algorithms
from cryptobench.shared.catalogue.key_types import entry_of, key_type, same_key_type
from cryptobench.shared.catalogue.provider_builds import ProviderBuilds


def test_a_spelling_reaches_its_canonical_entry():
    assert entry_of("Cipher", "aes/gcm/nopadding").id == "Cipher|AES/GCM/NoPadding"
    assert entry_of("Cipher", "NoSuchCipher/X/Y") is None


def test_the_key_type_is_the_one_every_build_of_the_provider_gives():
    assert key_type("Cipher", "PBEWithHmacSHA256AndAES_128") == "PBEWithHmacSHA256AndAES_128"
    assert key_type("Cipher", "PBEWithHmacSHA256AndAES_128", "AndroidOpenSSL") == "AES"
    assert key_type("Mac", "HmacSHA256", "NoSuchProvider") == "HMAC"
    assert key_type("Cipher", "NoSuchCipher/X/Y", "BC") is None


def test_builds_that_disagree_give_no_key_type():
    entry = entry_of("Cipher", "PBEWithHmacSHA256AndAES_128")
    builds = ProviderBuilds({"P @ android-26": {"name": "P"}, "P @ android-30": {"name": "P"}})
    raw = {**entry.raw, "providers": {"P @ android-30": {"key.type": "AES"}}}
    catalogue = Algorithms((Entry(entry.id, entry.family, raw),), algorithms().common)
    assert key_type("Cipher", "PBEWithHmacSHA256AndAES_128", "P", catalogue=catalogue, builds=builds) is None
    assert key_type("Cipher", "PBEWithHmacSHA256AndAES_128", "P @ android-30", catalogue=catalogue, builds=builds) == "AES"


def test_key_types_compare_through_the_names_files_vocabulary():
    assert same_key_type("HmacSHA256", "HMAC") and same_key_type("ec", "EC")
    assert not same_key_type("CHACHA", "ChaCha20")
    assert not same_key_type("RSASSA-PSS", "RSA")


def test_a_pss_generator_and_signature_take_their_own_key_type():
    assert key_type("KeyPairGenerator", "RSASSA-PSS", "SunRsaSign") == "RSASSA-PSS"
    assert key_type("Signature", "rsassa-pss", "BundledBC") == "RSASSA-PSS"
    assert key_type("Signature", "SHA256withRSA", "SunRsaSign") == "RSA"


def test_the_shared_fixture_reads_alike_in_python():
    cases = yaml.safe_load((paths.repo().contract_catalogue / "key-types.yaml").read_text())["cases"]
    assert [key_type(c["type"], c["name"], c["provider"]) for c in cases] == [c["keyType"] for c in cases]
