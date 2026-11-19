"""thermal.json as the session hooks write it, byte for byte; contracts/runner/thermal.json is the file the Kotlin reader test reads too."""
import json, pathlib

import fake_phone
from cryptobench.shared import paths
from test_thermal_gate import CASE, Heat
from test_device_benchmark_flow import measured

GOLDEN = paths.repo().contract_runner / paths.THERMAL


def test_a_gated_run_with_one_unreadable_start_writes_the_shared_golden(tmp_path, monkeypatch):
    # hot start: 240 s of waiting before a; the fifth reading (a's start) is unreadable, so a carries a note
    Heat(monkeypatch, start=45.0, rise=0.1, cooling=0.05, unreadable=(5,))
    _phone, _files, problems, results = measured(tmp_path, monkeypatch, CASE)
    assert problems == []
    assert (results / "benchmark/thermal.json").read_text() == GOLDEN.read_text()


def test_without_a_gate_the_document_ends_with_a_null_gate_and_no_case_has_one(tmp_path, monkeypatch):
    Heat(monkeypatch)
    _phone, _files, _problems, results = measured(tmp_path, monkeypatch, {})
    text = (results / "benchmark/thermal.json").read_text()
    document = json.loads(text)
    assert list(document) == ["schemaVersion", "process", "cases", "gate"] and text.endswith('\n "gate": null\n}')
    assert all("gate" not in reading for reading in document["cases"].values())


def test_convert_reads_the_gate_keys(tmp_path, monkeypatch):
    seen, real = [], fake_phone.fake_convert

    def convert(phone, arguments, words, notices):
        seen.append(json.loads(pathlib.Path(arguments.split("--thermal=")[1].split()[0]).read_text()))
        return real(phone, arguments, words, notices)
    monkeypatch.setattr(fake_phone, "fake_convert", convert)
    Heat(monkeypatch)
    measured(tmp_path, monkeypatch, CASE)
    [document] = seen
    assert document["gate"] == {"sensors": ["skin"], "kept": 36.0} and all("gate" in r for r in document["cases"].values())


def test_each_process_writes_only_its_own_gate_records(tmp_path, monkeypatch):
    Heat(monkeypatch, start=45.0, cooling=0.05)
    measured(tmp_path, monkeypatch, CASE | {"processRepetitions": 2})
    gates = [json.loads((tmp_path / f"results/benchmark/process-{n}/thermal.json").read_text())["cases"]["a"]["gate"] for n in (1, 2)]
    assert gates == [{"waitedSeconds": 240.0, "target": 35.75, "discards": 0}, {"waitedSeconds": 0.0, "target": 35.75, "discards": 0}]
