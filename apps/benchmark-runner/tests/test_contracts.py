"""contracts/: each shared YAML reads through cryptobench.shared.document.document to the value its .json holds, as the Kotlin owners' ContractsTest
read it; the files Python writes are byte for byte what its writers write. "current behaviour" tests pin a known split to flip on purpose."""
import json
import types

import pytest
import yaml

from cryptobench.stages.discovery import facts
from cryptobench.stages.configuration import guide
from cryptobench.stages.verification import known_answers
from cryptobench.shared.catalogue import guide_items, vectors
from cryptobench.shared.catalogue.names import NAMES_DOC, Canonical, Names
from cryptobench.shared import paths
from cryptobench.shared.document.document import parse_yaml, read_yaml

DOCUMENTS, CODEC = paths.repo().contract_documents, paths.repo().contract_yaml_codec
SHARED = {**dict.fromkeys(("global", "effective", "guide", "known-answers", "facts", "algorithm-names"), DOCUMENTS),
          **dict.fromkeys(("scalars", "python-strings"), CODEC)}
# the keys whose value Python and Kotlin read differently today, each pinned below
SPLIT = {"scalars": "exponentNoDot"}


def stated(name):
    return json.loads((SHARED[name] / f"{name}.json").read_text())


@pytest.mark.parametrize("name", SHARED)
def test_each_fixture_reads_to_its_stated_value(name):
    value = read_yaml(SHARED[name] / f"{name}.yaml")
    value.pop(SPLIT.get(name), None)
    assert value == stated(name)


def test_current_behaviour_an_unquoted_exponent_without_a_dot_is_a_string_in_python():
    # Kotlin's SnakeYAML reads the same plain 1e3 as the double 1000.0
    assert read_yaml(CODEC / "scalars.yaml")["exponentNoDot"] == "1e3"


def test_current_behaviour_python_writes_an_exponent_like_string_unquoted():
    # so a Python-written 1e3 reaches Kotlin as 1000.0; the Kotlin side pins that read
    text = (CODEC / "python-strings.yaml").read_text()
    assert yaml.safe_dump(stated("python-strings"), sort_keys=False) == text
    assert "  exponent: 1e3\n" in text and "  digits: '616263'\n" in text


def test_current_behaviour_a_duplicate_key_keeps_the_last_value():
    # Kotlin config and preparation refuse this file; discovery's codec and CaseDocument keep the last value too
    assert read_yaml(CODEC / "duplicate-key.yaml") == {"schemaVersion": 1, "run": {"seed": 2}, "seed": "last"}


def test_the_guide_writer_writes_the_shared_guide(tmp_path, monkeypatch):
    effective, capture = tmp_path / "effective.yaml", tmp_path / "probe.yaml"
    effective.write_text("providers: {}\n")
    capture.write_text("runtime: {sdkInt: 36}\n")
    monkeypatch.setattr(guide, "guide_items", lambda _effective, platform: stated("guide") if platform == "android-36" else None)
    assert guide.write(effective, capture).read_text() == (DOCUMENTS / "guide.yaml").read_text()
    assert stated("guide")["schemaVersion"] == guide_items.SCHEMA_VERSION


def test_the_known_answers_writer_writes_the_shared_known_answers(tmp_path, monkeypatch):
    effective, capture, configuration = tmp_path / "effective.yaml", tmp_path / "probe.yaml", tmp_path / "global.yaml"
    for path in (effective, capture, configuration):
        path.write_text("{}\n")
    monkeypatch.setattr(known_answers.vectors, "filled", lambda *_arguments: (stated("known-answers"), []))
    assert known_answers.write_known_answers(effective, capture, configuration).read_text() == (DOCUMENTS / "known-answers.yaml").read_text()
    assert stated("known-answers")["schemaVersion"] == vectors.SCHEMA_VERSION


def test_the_facts_writer_writes_the_shared_facts(tmp_path, monkeypatch):
    cores = [{"index": 0, "online": True, "cpuMaxKhz": 2246000}, {"index": 1, "online": False, "cpuMaxKhz": None},
             {"index": 7, "online": True, "cpuMaxKhz": 3782000}]
    monkeypatch.setattr(facts.captured, "read_runtime", lambda _capture: {"sdkInt": "37"})
    monkeypatch.setattr(facts.clocks, "read", lambda _device: cores)
    monkeypatch.setattr(facts, "rooted", lambda _device: False)
    monkeypatch.setattr(facts, "installed_abi", lambda _device: "arm64-v8a")
    monkeypatch.setattr(facts, "pinning", lambda _apk, _abi: True)
    build = {"securityPatch": "2026-10-05", "apex": {"com.android.conscrypt": 360910000, "com.android.art": 360910000}}
    written = facts.gather(types.SimpleNamespace(), tmp_path, tmp_path / "probe.yaml", build)
    assert written.read_text() == (DOCUMENTS / "facts.yaml").read_text()


def test_the_names_fixture_passes_the_python_reader_and_resolves_as_kotlin_resolves_it():
    assert NAMES_DOC.read(DOCUMENTS / "algorithm-names.yaml")["schemaVersion"] == 1
    names = Names.load(DOCUMENTS / "algorithm-names.yaml")
    # the same four lookups AlgorithmNames answers in the config module's ContractsTest
    assert names.canonical("MessageDigest", "sha") == Canonical("SHA-1")
    assert names.canonical("Cipher", "tripledes") == Canonical("DESede")
    assert names.canonical("Cipher", "AES_256") == Canonical("AES", 256)
    assert names.canonical("Cipher", "ChaCha20") == Canonical("ChaCha20", None, False)


def test_a_fixture_parses_the_same_through_parse_yaml_and_read_yaml():
    text = (DOCUMENTS / "effective.yaml").read_text()
    assert parse_yaml(text, "effective.yaml") == read_yaml(DOCUMENTS / "effective.yaml")
