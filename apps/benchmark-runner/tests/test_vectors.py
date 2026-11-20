"""Known answers: what stops a run, what is only reported, and how one vector fills per provider."""
import pathlib

import pytest
import yaml

from cryptobench.shared.catalogue import vectors  # noqa: E402
from cryptobench.shared.errors.input_error import InputError  # noqa: E402

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "benchmark/modules/benchmark/src/test/resources/known-answers-fixture.yaml"
VECTOR = {"id": "mine", "source": "s", "type": "Cipher", "algorithm": "ChaCha20", "operations": ["ENCRYPT"], "input": "00", "output": "00"}


def folder(tmp_path, *entries, name="cipher.secret.yaml"):
    tmp_path.joinpath(name).write_text(yaml.safe_dump({"schemaVersion": 1, "vectors": list(entries)}))
    return tmp_path


def test_every_guide_id_exists_and_packaged_vectors_are_all_named():
    assert vectors.checked(vectors.load()) == []


def test_the_kotlin_fixture_keeps_the_published_answers():
    packaged = vectors.load()
    for vector in yaml.safe_load(FIXTURE.read_text())["vectors"]:
        assert (vector["input"], vector["output"], vector.get("key")) == (packaged[vector["id"]]["input"], packaged[vector["id"]]["output"], packaged[vector["id"]].get("key"))


def test_a_missing_user_folder_stops(tmp_path):
    with pytest.raises(InputError, match="vectors_folder_missing"):
        vectors.load(tmp_path / "typo")


def test_a_user_vector_cannot_replace_a_packaged_id(tmp_path):
    with pytest.raises(InputError, match="duplicate_id"):
        vectors.load(folder(tmp_path, {**VECTOR, "id": "sha1-abc"}))


def test_a_malformed_vector_stops_naming_the_field(tmp_path):
    with pytest.raises(InputError, match="unknown fields"):
        vectors.load(folder(tmp_path, {**VECTOR, "nonse": "00"}))
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(InputError, match="no family"):
        vectors.load(folder(other, VECTOR, name="made.up.yaml"))


SHA256 = {"id": "mine-sha256", "source": "s", "type": "MessageDigest", "algorithm": "SHA256", "operations": ["DIGEST"], "input": "616263",
          "output": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}
ECB = {"id": "mine-ecb", "source": "s", "type": "Cipher", "algorithm": "AES/ECB/NoPadding", "operations": ["ENCRYPT", "DECRYPT"],
       "key": {"algorithm": "AES", "secret": "2b7e151628aed2a6abf7158809cf4f3c"}, "input": "6bc1bee22e409f96e93d7e117393172a", "output": "3ad77bb40d7a3660a89ecaf32466ef97"}


def user_fill(tmp_path, effective, *entries, name):
    document, warnings = vectors.filled(effective, "jdk-25", folder(tmp_path, *entries, name=name))
    return [v for v in document["vectors"] if v["origin"] == "user"], warnings


def test_a_user_vector_no_entry_names_is_no_guide_warning(tmp_path):
    assert vectors.checked(vectors.load(folder(tmp_path, VECTOR))) == []


def test_a_user_vector_reaches_the_case_its_name_or_alias_matches(tmp_path):
    got, warnings = user_fill(tmp_path, {"providers": {"SUN": {"MessageDigest": {"SHA-256": {}}}}}, SHA256, name="digest.none.yaml")
    assert [(v["id"], v["provider"], v["algorithm"]) for v in got] == [("mine-sha256", "SUN", "SHA-256")]
    assert warnings == []


def test_a_user_vector_of_another_key_size_or_operation_matches_no_case(tmp_path):
    effective = {"providers": {"SunJCE": {"Cipher": {"AES/ECB/NOPADDING": {"keySizes": [256]}}}}}
    got, warnings = user_fill(tmp_path, effective, ECB, {**ECB, "id": "mine-sign", "key": {"algorithm": "AES", "secret": "00" * 32}, "operations": ["SIGN"]}, name="cipher.secret.yaml")
    assert got == []
    assert warnings == [f"orphan_vector: {i} matches no case of this run by type, name or alias, operation and key size" for i in ("mine-ecb", "mine-sign")]
    got, warnings = user_fill(tmp_path, {"providers": {"SunJCE": {"Cipher": {"AES/ECB/NOPADDING": {"keySizes": [128, 256]}}}}}, ECB, name="cipher.secret.yaml")
    assert [v["id"] for v in got] == ["mine-ecb"] and warnings == []


def fills(platform, provider="AndroidOpenSSL"):
    effective = {"providers": {provider: {"Cipher": {"ChaCha20": {}}}}}
    return {v["id"]: v for v in vectors.filled(effective, platform)[0]["vectors"]}


def test_a_counter_0_provider_runs_the_counter_0_vector_only():
    got = fills("android-36")
    assert got["chacha20-rfc8439-a2-1"]["parameters"] == {"class": "javax.crypto.spec.IvParameterSpec", "arguments": [{"hex": "00" * 12}]}
    assert "fixes it at 0" in got["chacha20-rfc8439-2.4.2"]["unexpressible"]


def test_a_counter_1_provider_runs_the_counter_1_vector_only():
    got = fills("jdk-25", "SunJCE")
    assert got["chacha20-rfc8439-2.4.2"]["parameters"]["arguments"] == [{"hex": "000000000000004a00000000"}, 1]
    assert "fixes it at 1" in got["chacha20-rfc8439-a2-1"]["unexpressible"]


def test_a_run_with_no_compared_vector_says_so():
    _, compared = vectors.coverage([{"case": {"type": "MessageDigest", "algorithm": "MD5"}, "oracles": {"knownAnswer": {"verdict": "not_checkable", "reason": "no_vector: x"}}}])
    assert not compared


def test_a_user_sign_vector_on_a_randomized_signature_stops(tmp_path):
    ecdsa = {"id": "mine-ecdsa", "source": "s", "type": "Signature", "algorithm": "SHA256withECDSA", "operations": ["SIGN", "VERIFY"], "input": "00", "output": "00"}
    with pytest.raises(InputError, match="vector_on_randomized_operation: mine-ecdsa"):
        user_fill(tmp_path, {"providers": {"SunEC": {"Signature": {"SHA256withECDSA": {}}}}}, ecdsa, name="signature.pair.yaml")
