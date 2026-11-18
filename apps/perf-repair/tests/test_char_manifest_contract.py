"""Characterization (Py-P8): the runner's manifest() read by perf-repair's BenchmarkManifest: the fields it keeps and the ones it drops; the delta
merge rewrites the raw manifest dict, so what the reader drops survives a merge."""
import json
from pathlib import Path

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


def test_today_the_reader_drops_problems_resumed_partial_and_energy(tmp_path):
    doc = runner_manifest(tmp_path)
    read = BenchmarkManifest.from_json(doc).to_json()
    assert sorted(set(doc) - set(read)) == ["energy", "partial", "problems", "resumed"]
    assert all(read[k] == doc[k] for k in ("mode", "config", "deviceId", "runtime", "providers", "files", "counts", "inputs", "operations"))
    assert doc["units"] == {"latency": "us"} and read["units"] == {"latency": "us", "throughput": "MB/s"}


def test_today_the_reader_drops_what_the_delta_merge_adds(tmp_path):
    doc = runner_manifest(tmp_path) | {"deltas": [{"session": "s"}], "retried": ["a"]}
    assert not {"deltas", "retried"} & set(BenchmarkManifest.from_json(doc).to_json())


def test_today_a_delta_merge_rewrites_the_raw_manifest_keeping_what_the_reader_drops(tmp_path):
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
