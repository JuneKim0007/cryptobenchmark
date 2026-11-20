"""The runner's manifest() read by perf-repair's BenchmarkManifest gives back every field as written; the delta merge writes through it."""
import json
from pathlib import Path

import pytest
import yaml

from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.results.manifest import manifest
from perfrepair.device.delta_merge import merge_delta
from perfrepair.dto import BenchmarkManifest

PROBE = {"schemaVersion": 1, "runtime": {"model": "probed", "sdkInt": 36, "fingerprint": "a/b/c:16/X/1:user/release-keys"},
         "providers": [{"name": "P", "precedence": 1, "services": [{"type": "t", "algorithm": "a"}]}]}


def written(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def runner_manifest(folder):
    files = {"probe": written(folder / "discovery/probe_1.yaml", yaml.safe_dump(PROBE)),
             "effective": written(folder / "configuration/effective.yaml", "analysis: {units: {latency: us}}\n"),
             "benchmark": written(folder / "benchmark/benchmark.json", json.dumps({"runtime": {"model": "m"}, "cases": [{"id": "a", "metrics": {"timeNs": {"runs": [1.0]}}}]})),
             "energy": written(folder / "benchmark/energy.json", json.dumps({"source": "manafa", "kind": "estimated"}))}
    config = written(folder / "global.yaml", "schemaVersion: 1\n")
    manifest(folder, "device", config, files, ["energy_failed: x"], partial={"reason": "interrupted"}, resumed=[{"pass": "timing"}])
    return read_yaml(folder / "manifest.yaml")


def test_the_reader_gives_back_the_written_manifest(tmp_path):
    doc = runner_manifest(tmp_path)
    read = BenchmarkManifest.from_json(doc)
    assert list(read.to_json().items()) == list(doc.items())
    assert read.problems == ("energy_failed: x",) and read.partial == {"reason": "interrupted"} and read.energy["kind"] == "estimated"
    assert read.display_units.throughput == "MB/s"


def test_the_reader_keeps_what_the_delta_merge_adds(tmp_path):
    doc = runner_manifest(tmp_path) | {"deltas": [{"session": "s"}], "retried": ["a"]}
    assert BenchmarkManifest.from_json(doc).to_json() == doc


def test_an_unknown_mode_or_schema_is_refused(tmp_path):
    doc = runner_manifest(tmp_path)
    for bad in ({"mode": "phone"}, {"schemaVersion": 0}):
        with pytest.raises(Exception):
            BenchmarkManifest.from_json(doc | bad)


def test_a_delta_merge_keeps_every_field_and_writes_through_the_runner(tmp_path):
    stored, staged = tmp_path / "stored", tmp_path / "staged"
    before = runner_manifest(stored)
    runner_manifest(staged)
    (staged / "benchmark/benchmark.json").write_text(json.dumps({"cases": [{"id": "b", "metrics": {"timeNs": {"runs": [2.0]}}}]}))
    merge_delta(stored, staged, {"b"}, "s2", "same_session")
    after = read_yaml(stored / "manifest.yaml")
    assert list(after)[:len(before)] == list(before) and list(after)[len(before):] == ["deltas"]
    assert {k: after[k] for k in ("problems", "partial", "energy", "resumed", "units", "operations")} == \
           {k: before[k] for k in ("problems", "partial", "energy", "resumed", "units", "operations")}
    assert after["files"]["benchmark"] == str(Path("benchmark/merged-s2/benchmark.json")) and after["counts"]["measured"] == 2
    assert (stored / "manifest.yaml").stat().st_mode & 0o777 == 0o600
