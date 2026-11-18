"""A short energy window is launched once more aiming at 1.5 x the minimum, separate from the retries; still short is short_window."""
import json
import types

import yaml

from cryptobench.stages.measurement.session import dynamic_temperature, launch, window


def pulled_file(path, repeat, runs):
    path.write_text(json.dumps({"benchmarks": [{"name": "measure[a]", "repeatIterations": repeat, "warmupIterations": 1,
                                                "metrics": {"timeNs": {"runs": runs}}}]}))


def run(tmp_path, monkeypatch, windows):
    """windows: the (repeatIterations, runs) each launch pulls; returns the samples each launch asked for, the process and the outcome."""
    pulled, asked, left = tmp_path / "a.json", [], list(windows)

    def launched(_device, _class, arguments, _case, into):
        asked.append(arguments[-1])
        pulled_file(into, *left.pop(0))
    monkeypatch.setattr(launch.case_isolation, "launch_case", launched)
    sizing = window.MinWindow(5, 10, lambda samples: ("-e", "cryptobench.samples", str(samples)))
    plan = types.SimpleNamespace(gate=dynamic_temperature.Off(), retries=0, test_class="T", arguments=("-e", "cryptobench.samples", "10"), sizing=sizing)
    process = types.SimpleNamespace(samples={}, start_reading=None, end_reading=None)
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
