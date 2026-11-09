"""Known answers: what stops a run, what is only reported, and how one vector fills per provider."""
import pathlib

import pytest
import yaml

from stages import guide  # noqa: E402
from cryptobench.catalogue import vectors  # noqa: E402
from cryptobench.coded import InputError  # noqa: E402

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


def test_a_user_vector_no_entry_names_is_a_warning(tmp_path):
    assert vectors.checked(vectors.load(folder(tmp_path, VECTOR))) == ["orphan_vector: mine is named by no guide entry"]


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


def test_user_folder_is_relative_to_the_global_file(tmp_path):
    settings = tmp_path / "g.yaml"
    settings.write_text(yaml.safe_dump({"selection": {"testSet": "t", "knownVectors": "mine"}}))
    assert guide.user_vectors(settings) == tmp_path / "mine"
