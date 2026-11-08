"""Hooks around a device session that fail: a case hook costs its case, a process hook closes what opened, Ctrl-C stops the device."""
import json, pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from session import measure as measure_session  # noqa: E402
from fake_phone import Phone  # noqa: E402


class Recorded(measure_session.Hooks):
    """Logs every step to the phone's log; raises at the step and case named."""

    def __init__(self, phone, name, fails=None, case=None, error=RuntimeError):
        self.phone, self.name, self.fails, self.case, self.error = phone, name, fails, case, error

    def step(self, step, case=None):
        self.phone.log.append(f"{self.name}.{step}" + (f" {case}" if case else ""))
        if step == self.fails and case == self.case:
            raise self.error(f"{self.name} {step} broke")

    def before_process(self, process):
        self.step("before_process")

    def before_case(self, process, case):
        self.step("before_case", case)

    def after_case(self, process, case, failure):
        self.step("after_case", case)

    def after_process(self, process):
        self.step("after_process")

    def abandon(self, process):
        self.phone.log.append(f"{self.name}.abandon")


def session(phone, tmp_path, hooks, problems, converted=None):
    plan = measure_session.Plan("CryptoBenchmark", (), after_process=lambda process: phone.log.append("convert"))
    return measure_session.run_session(phone, plan, 1, "case", hooks, lambda _repetition: tmp_path / "benchmark", problems)


def hook_steps(phone):
    return [line for line in phone.log if "." in line or line in ("convert", "force-stop")]


@pytest.mark.parametrize("step", ["before_case", "after_case"])
def test_a_case_hook_that_fails_costs_that_case_only(tmp_path, step):
    phone, problems = Phone(tmp_path, cases=("a", "b", "c")), []
    hooks = [Recorded(phone, "outer"), Recorded(phone, "inner", fails=step, case="b")]
    process, = session(phone, tmp_path, hooks, problems)
    assert problems == [f"case_failed: b: hook_failed: Recorded.{step}: RuntimeError: inner {step} broke"]
    assert [b["name"] for b in json.loads(process.data.read_text())["benchmarks"]] == ["measure[a]", "measure[c]"]
    ran = [s for s in phone.log if s.startswith("instrument")]
    assert ran == (["instrument CryptoBenchmark a", "instrument CryptoBenchmark c"] if step == "before_case" else
                   ["instrument CryptoBenchmark a", "instrument CryptoBenchmark b", "instrument CryptoBenchmark c"])
    around_b = [s for s in hook_steps(phone) if s.endswith(" b")]
    assert around_b == (["outer.before_case b", "inner.before_case b", "outer.after_case b"] if step == "before_case" else
                        ["outer.before_case b", "inner.before_case b", "inner.after_case b", "outer.after_case b"])
    assert hook_steps(phone)[-3:] == ["inner.after_process", "outer.after_process", "convert"]


def test_a_case_hook_failing_on_every_case_fails_the_process_as_every_failed_case_does(tmp_path):
    phone = Phone(tmp_path, cases=("a",))
    with pytest.raises(measure_session.DeviceError, match="hook_failed: Recorded.before_case"):
        session(phone, tmp_path, [Recorded(phone, "only", fails="before_case", case="a")], [])


def test_a_process_hook_that_fails_to_start_closes_what_the_hooks_before_it_opened(tmp_path):
    phone = Phone(tmp_path, cases=("a",))
    hooks = [Recorded(phone, "window"), Recorded(phone, "clocks", fails="before_process"), Recorded(phone, "later")]
    with pytest.raises(RuntimeError, match="clocks before_process broke"):
        session(phone, tmp_path, hooks, [])
    assert hook_steps(phone) == ["window.before_process", "clocks.before_process", "clocks.abandon", "window.abandon"]
    assert not [s for s in phone.log if s.startswith("instrument")]
