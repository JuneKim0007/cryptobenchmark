"""A short energy window is launched once more aiming at 1.5 x the minimum, separate from the retries; still short is short_window."""
import json
import types

import yaml

from cryptobench.stages.measurement.session import dynamic_temperature, launch, measure, window
from cryptobench.stages.measurement.validation import expectation


def pulled_file(path, repeat, runs):
    path.write_text(json.dumps({"benchmarks": [{"name": "measure[a]", "repeatIterations": repeat, "warmupIterations": 1,
                                                "metrics": {"timeNs": {"runs": runs}}}]}))


def run(tmp_path, monkeypatch, windows, sizing=None, repetition=1):
    """windows: the (repeatIterations, runs) each launch pulls; returns the samples each launch asked for, the process and the outcome."""
    pulled, asked, left = tmp_path / f"benchmark/process-{repetition}/cases/a.json", [], list(windows)
    pulled.parent.mkdir(parents=True)

    def launched(_device, _class, arguments, _case, into):
        asked.append(arguments[-1])
        pulled_file(into, *left.pop(0))
    monkeypatch.setattr(launch.case_isolation, "launch_case", launched)
    sizing = sizing or window.MinWindow(5, 10, lambda samples: ("-e", "cryptobench.samples", str(samples)))
    plan = types.SimpleNamespace(gate=dynamic_temperature.Off(), retries=0, test_class="T", arguments=("-e", "cryptobench.samples", "10"), sizing=sizing,
                                 unit=tmp_path, expectation=expectation.Expectation("energy", 10, 5))
    process = measure.Process(repetition, pulled.parents[1])
    return asked, process, launch.run_of_case(None, plan, process, "a", [], pulled), sizing


def test_a_long_window_runs_once(tmp_path, monkeypatch):
    asked, process, outcome, _ = run(tmp_path, monkeypatch, [(1000, [1e6] * 10)])
    assert (asked, outcome, process.samples) == (["10"], None, {"a": {"samples": 10, "windowSeconds": 10.0}})


def test_a_short_window_is_launched_once_with_samples_for_one_and_a_half_times_the_minimum(tmp_path, monkeypatch, capsys):
    asked, process, outcome, sizing = run(tmp_path, monkeypatch, [(1000, [2e5] * 10), (1000, [2e5] * 38)])
    assert (asked, outcome) == (["10", "38"], None)
    assert process.samples == {"a": {"samples": 10, "windowSeconds": 2.0, "relaunched": {"samples": 38, "windowSeconds": 7.6}}}
    assert "window:    a: 2.00 s below 5 s; launching again with 38 samples" in capsys.readouterr().out
    written = yaml.safe_load(sizing.write(process, tmp_path / "energy-samples.yaml").read_text())
    assert written == {"schemaVersion": 1, "minWindowSeconds": 5, "cases": process.samples}


def test_still_short_after_the_relaunch_is_flagged_and_kept_not_launched_again(tmp_path, monkeypatch, capsys):
    asked, process, outcome, _ = run(tmp_path, monkeypatch, [(1000, [2e5] * 10), (1000, [1e5] * 38)])
    assert (asked, outcome, process.samples["a"]["shortWindow"]) == (["10", "38"], None, True)
    assert "warning: short_window: a: 3.80 s with 38 samples, below 5 s" in capsys.readouterr().out


def test_a_relaunch_that_fails_every_retry_keeps_the_short_window_flagged(tmp_path, monkeypatch, capsys):
    pulled, left = tmp_path / "benchmark/cases/a.json", [(1000, [2e5] * 10)]
    pulled.parent.mkdir(parents=True)

    def launched(_device, _class, _arguments, _case, into):
        if not left:
            into.unlink(missing_ok=True)
            return "case_failed: a: Process crashed."
        pulled_file(into, *left.pop(0))
    monkeypatch.setattr(launch.case_isolation, "launch_case", launched)
    sizing = window.MinWindow(5, 10, lambda samples: ("-e", "cryptobench.samples", str(samples)))
    plan = types.SimpleNamespace(gate=dynamic_temperature.Off(), retries=1, test_class="T", arguments=(), sizing=sizing, unit=tmp_path,
                                 expectation=expectation.Expectation("energy", 10, 5), refused=lambda _case: None,
                                 reconnect=types.SimpleNamespace(retried=lambda step, _what: step()))
    process = measure.Process(1, tmp_path / "benchmark")
    assert launch.run_of_case(None, plan, process, "a", [], pulled) is None
    assert json.loads(pulled.read_text())["benchmarks"][0]["metrics"]["timeNs"]["runs"] == [2e5] * 10
    assert process.samples == {"a": {"samples": 10, "windowSeconds": 2.0, "shortWindow": True}}
    assert [entry["code"] for entry in process.relaunched] == ["short_window", "case_failed"]
    assert sizing.decided == {"a": 10}
    assert "warning: short_window: a: 2.00 s with 10 samples kept, below 5 s; its relaunch failed: case_failed: a: Process crashed." in capsys.readouterr().out


def test_a_later_process_launches_the_count_the_first_decided_and_only_flags_a_short_window(tmp_path, monkeypatch, capsys):
    asked, first, _, sizing = run(tmp_path, monkeypatch, [(1000, [2e5] * 10), (1000, [2e5] * 38)])
    assert asked == ["10", "38"] and sizing.decided == {"a": 38}
    asked, second, outcome, _ = run(tmp_path, monkeypatch, [(1000, [1.2e5] * 38)], sizing, repetition=2)
    assert (asked, outcome) == (["38"], None)
    assert second.samples == {"a": {"samples": 38, "windowSeconds": 4.56, "shortWindow": True}}
    assert "warning: short_window: a: 4.56 s with 38 samples, below 5 s; sized by an earlier process" in capsys.readouterr().out
    asked, third, _, _ = run(tmp_path, monkeypatch, [(1000, [1e6] * 38)], sizing, repetition=3)
    assert asked == ["38"] and third.samples == {"a": {"samples": 38, "windowSeconds": 38.0}}


def test_a_long_first_window_decides_the_pass_count(tmp_path, monkeypatch):
    _, _, _, sizing = run(tmp_path, monkeypatch, [(1000, [1e6] * 10)])
    asked, _, _, _ = run(tmp_path, monkeypatch, [(1000, [2e5] * 10)], sizing, repetition=2)
    assert sizing.decided == {"a": 10} and asked == ["10"]


def test_a_kept_process_seeds_the_counts_and_a_missing_file_seeds_none(tmp_path):
    sizing = window.MinWindow(5, 10, lambda samples: ("-e", "cryptobench.samples", str(samples)))
    kept = tmp_path / "energy-samples.yaml"
    kept.write_text(yaml.safe_dump({"schemaVersion": 1, "minWindowSeconds": 5, "cases": {
        "a": {"samples": 10, "windowSeconds": 2.0, "relaunched": {"samples": 38, "windowSeconds": 7.6}}, "b": {"samples": 10, "windowSeconds": 9.0}}}))
    sizing.seeded(tmp_path / "absent.yaml")
    assert sizing.decided == {}
    sizing.seeded(kept)
    assert sizing.decided == {"a": 38, "b": 10} and sizing.first("a") == (("-e", "cryptobench.samples", "38"), 38)
    assert sizing.first("c") == (("-e", "cryptobench.samples", "10"), 10)
