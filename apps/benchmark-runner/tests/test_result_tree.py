"""The files a fake-phone device run leaves in its device folder, manifest included, as a sorted list."""
import yaml

from cryptobench.shared.results.manifest import manifest
from test_device_benchmark_flow import DUMP, MEASURED, measured
from fake_phone import PROBE

COMMON = ["benchmark/benchmark.json", "configuration/effective.yaml", "discovery/probe_1.yaml", "discovery/trial_1.yaml", "global.yaml",
          "manifest.yaml", "preparation/prepared.yaml", "preparation/skipped.yaml", "validation.yaml"]


def tree(tmp_path, monkeypatch, run, **phone):
    _phone, files, problems, results = measured(tmp_path, monkeypatch, run, **phone)
    files["probe"] = results / "discovery/probe_1.yaml"
    files["probe"].write_text(yaml.safe_dump(PROBE))
    (results / "global.yaml").write_text("schemaVersion: 1\n")
    manifest(results, "device", results / "global.yaml", files, problems)
    return sorted(p.relative_to(results).as_posix() for p in results.rglob("*") if p.is_file()), files


def test_one_pass_one_process_per_case(tmp_path, monkeypatch):
    found, files = tree(tmp_path, monkeypatch, {}, thermal=DUMP)
    assert found == sorted(COMMON + ["benchmark/benchmarkData.json", "benchmark/cases/a.json", "benchmark/cases/b.json",
                                     "benchmark/clocks.yaml", "benchmark/order.txt", "benchmark/thermal.json", "benchmark/blocks/block-1.yaml"])
    assert list(files) == ["effective", "clocks", "prepared", "skipped", "benchmark", "probe"]


def test_two_repetitions(tmp_path, monkeypatch):
    found, _files = tree(tmp_path, monkeypatch, {"processRepetitions": 2})
    per_process = [f"benchmark/process-{n}/{name}" for n in (1, 2) for name in
                   ("benchmark.json", "benchmarkData.json", "cases/a.json", "cases/b.json", "clocks.yaml", "order.txt", "thermal.json")]
    assert found == sorted(COMMON + per_process + ["benchmark/blocks/block-1.yaml"])


def test_an_energy_and_a_timing_pass(tmp_path, monkeypatch):
    found, _files = tree(tmp_path, monkeypatch, MEASURED)
    per_pass = [f"benchmark/{folder}/{name}" for folder in ("energy", "timing") for name in
                ("benchmark.json", "benchmarkData.json", "cases/a.json", "cases/b.json", "clocks.yaml", "order.txt", "thermal.json")]
    blocks = [f"benchmark/{folder}/blocks/block-1.yaml" for folder in ("energy", "timing")]
    assert found == sorted(COMMON + per_pass + blocks + ["benchmark/energy/energy.json", "benchmark/energy/energy-samples.yaml", "discovery/energy.yaml"])
