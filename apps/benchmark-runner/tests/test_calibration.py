import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from session import calibration, case_isolation  # noqa: E402


def data(tmp_path, repeat=70_000, ns=1600.0, warmup=1000):
    file = tmp_path / "benchmarkData.json"
    file.write_text(json.dumps({"benchmarks": [{"name": "measure[a]", "repeatIterations": repeat, "warmupIterations": warmup,
                                                "metrics": {"timeNs": {"runs": [ns, ns, ns]}}}]}))
    return file


def test_a_collapsed_sample_is_named_and_a_normal_one_is_not(tmp_path):
    assert calibration.short_samples(data(tmp_path)) == []
    assert calibration.short_samples(data(tmp_path, repeat=1, ns=38_000.0))[0].startswith("miscalibrated: measure[a]: 1 calls")


def test_a_warmup_near_the_cap_is_noted_only_when_the_samples_are_usable(tmp_path):
    assert "warmup_near_cap" in calibration.near_cap(data(tmp_path, warmup=4_500_000))[0]
    assert calibration.near_cap(data(tmp_path, warmup=1000)) == []
    assert calibration.near_cap(data(tmp_path, repeat=1, ns=38_000.0, warmup=4_500_000)) == []


def launches(monkeypatch, tmp_path, repeats):
    file = tmp_path / "pulled.json"
    calls = []

    def launch(_device, _test, _arguments, _case, pulled):
        calls.append(1)
        data(tmp_path, repeat=repeats[len(calls) - 1]).rename(pulled)
    monkeypatch.setattr(case_isolation, "launch_case", launch)
    return case_isolation.measure_case(None, "T", (), "a", file), len(calls)


def test_a_collapsed_launch_is_measured_again_and_kept_if_the_second_is_good(monkeypatch, tmp_path):
    assert launches(monkeypatch, tmp_path, [1, 70_000]) == (None, 2)


def test_two_collapsed_launches_fail_the_case(monkeypatch, tmp_path):
    failure, count = launches(monkeypatch, tmp_path, [1, 1])
    assert count == 2 and failure.startswith("case_failed: a: miscalibrated")


def test_a_good_launch_runs_once(monkeypatch, tmp_path):
    assert launches(monkeypatch, tmp_path, [70_000]) == (None, 1)
