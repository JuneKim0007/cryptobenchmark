"""The pass every other merges into: timing when present, else the single pass itself."""
from unittest import mock

from cryptobench.stages.measurement.session import passes  # noqa: E402


def merged_base(tmp_path, names):
    results = {passes.Pass(name, 5, ("TIME",)): (tmp_path / name / "benchmark.json", []) for name in names}
    with mock.patch.object(passes.gradle_runner, "run") as run:
        passes.merged(results, tmp_path, 1, mock.Mock(stacktrace=False, stream=False))
    return run.call_args.args[0].split()[1]


def test_timing_is_the_base_when_present(tmp_path):
    assert merged_base(tmp_path, ["energy", "timing"]).endswith("timing/benchmark.json")


def test_a_single_energy_pass_is_its_own_base(tmp_path):
    assert merged_base(tmp_path, ["energy"]).endswith("energy/benchmark.json")
