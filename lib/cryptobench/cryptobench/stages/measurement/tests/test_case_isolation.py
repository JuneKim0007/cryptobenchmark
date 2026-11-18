"""One process per case over a fake instrumentation: one case aborts its process, the others still produce results."""
import json
import pathlib

import pytest

from cryptobench.stages.measurement import case_files  # noqa: E402
from cryptobench.stages.measurement.session import case_isolation  # noqa: E402
from cryptobench.stages.measurement.session import measure as measure_session  # noqa: E402
from cryptobench.stages.measurement.session import variant_order  # noqa: E402
from fake_phone import jetpack_case, listed, OK, Phone  # noqa: E402


def session(phone, tmp_path, problems=None):
    plan = measure_session.Plan("CryptoBenchmark", ("-e", "x", "y"), listed)
    return measure_session.run_session(phone, plan, 1, [], lambda _repetition: tmp_path / "benchmark",
                                       [] if problems is None else problems)


def test_a_case_that_kills_its_process_loses_only_itself(tmp_path):
    phone, problems = Phone(tmp_path, cases=("a", "crash", "b", "hang"), crash=("crash",), hang=("hang",)), []
    process, = session(phone, tmp_path, problems)
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]
    assert [line.split(": ")[:2] for line in problems] == [["case_failed", "crash"], ["case_failed", "hang"]]
    assert "force-stop" in phone.log
    assert sorted(p.name for p in (process.into / "cases").iterdir()) == ["a.json", "b.json"]


def test_the_merged_file_is_the_one_the_kept_case_files_give_and_a_file_already_there_is_never_deleted(tmp_path):
    stale = tmp_path / "benchmark/cases/old.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    process, = session(Phone(tmp_path, cases=("a", "b")), tmp_path)
    kept = [json.loads((process.into / "cases" / f"{case}.json").read_text()) for case in ("a", "b")]
    expected = {"context": kept[0]["context"], "benchmarks": [b for document in kept for b in document["benchmarks"]]}
    assert process.data.read_text() == json.dumps(expected, indent=1) and stale.read_text() == "{}"


def test_the_listing_is_the_planned_cases_in_order():
    listing = "".join(f"INSTRUMENTATION_STATUS: test=measure[{case}]\n" for case in ("a", "crash", "b", "hang"))
    assert case_isolation.listed(listing + listing) == ["a", "crash", "b", "hang"]


def test_one_data_file_from_many_cases_keeps_the_first_context_in_the_order_given(tmp_path):
    case_files.opened(tmp_path)
    for case, n in (("x", 1), ("y", 2), ("z", 3)):
        case_files.path(tmp_path, case).write_text(json.dumps({"context": {"n": n}, "benchmarks": [{"name": case}]}))
    case_files.merge(tmp_path, ["y", "x"], tmp_path / "benchmarkData.json")
    assert json.loads((tmp_path / "benchmarkData.json").read_text()) == {"context": {"n": 2}, "benchmarks": [{"name": "y"}, {"name": "x"}]}


def test_an_error_that_ends_the_session_keeps_every_case_measured_before_it(tmp_path, monkeypatch):
    phone = Phone(tmp_path, cases=("a", "b", "c"))
    cleared = phone.shell

    def offline(command):
        if command.startswith(f"rm -f {phone.data}") and ("instrument CryptoBenchmark b") in phone.log:
            raise measure_session.DeviceError("adb shell: device offline")
        return cleared(command)
    monkeypatch.setattr(phone, "shell", offline)
    with pytest.raises(measure_session.DeviceError, match="device offline"):
        session(phone, tmp_path)
    data = tmp_path / "benchmark/benchmarkData.json"
    assert [b["name"] for b in json.loads(data.read_text())["benchmarks"]] == ["measure[a]", "measure[b]"]


def test_a_seeded_order_is_the_order_the_cases_launch_in_and_is_written_beside_them(tmp_path):
    cases = tuple("abcdefgh")
    phone = Phone(tmp_path, cases=cases)
    plan = measure_session.Plan("CryptoBenchmark", ("-e", "x", "y"), order=variant_order.shuffled(5))
    processes = measure_session.run_session(phone, plan, 2, [], lambda r: tmp_path / f"process-{r}", [])
    launched = [named for _test, named in phone.ran if named]
    assert launched == [case for process in processes for case in process.cases]
    for process in processes:
        assert process.cases == variant_order.shuffled(5)(process.repetition, list(cases))
        assert (process.into / "order.txt").read_text().split() == process.cases
        assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == [f"measure[{c}]" for c in process.cases]
    assert processes[0].cases != processes[1].cases


class Stale(Phone):
    """The pulled file of `stale` names the cases `written`: an earlier result the device kept, or none."""

    def __init__(self, folder, stale, written, **options):
        super().__init__(folder, **options)
        self.stale, self.stale_written, self.serving = stale, written, False

    def instrument(self, test_class, *arguments, step="instrument"):
        self.serving = self.stale in arguments
        return super().instrument(test_class, *arguments, step=step)

    def pulled(self, remote, local, check):
        if remote == self.data and self.serving:
            pathlib.Path(local).write_text(json.dumps({"context": {}, "benchmarks": [jetpack_case(c) for c in self.stale_written]}))
            return OK
        return super().pulled(remote, local, check)


@pytest.mark.parametrize("name", ["measure[b]", "EMULATOR_measure[b]", "DEBUGGABLE_EMULATOR_measure[b]"])
def test_the_error_ids_androidx_prefixes_still_name_the_case(name):
    assert case_isolation.SUPPRESSED_PREFIX.sub("", name) == "measure[b]"
    assert case_isolation.SUPPRESSED_PREFIX.sub("", "EMULATOR_measure[a]") != "measure[b]"


@pytest.mark.parametrize("written, named", [(["a"], "measure[a]"), ([], "no benchmark")], ids=["another case", "no benchmark"])
def test_a_pulled_result_that_names_another_case_is_refused_and_never_stored(tmp_path, written, named):
    phone, problems = Stale(tmp_path, "b", written, cases=("a", "b", "c")), []
    process, = session(phone, tmp_path, problems)
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[c]"]
    assert problems == [f"case_failed: b: result_mismatch: the pulled benchmarkData.json names {named}, not measure[b]; not stored"]
    assert sorted(p.name for p in (process.into / "cases").iterdir()) == ["a.json", "c.json"]
