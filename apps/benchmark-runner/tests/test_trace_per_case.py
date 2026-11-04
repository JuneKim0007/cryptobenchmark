import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from energy_session import EnergySession  # noqa: E402


class Phone:
    """A device where each case's process leaves only its own trace in the media folder."""
    media = "/media"

    def __init__(self):
        self.on_device = []

    def run_case(self, case):
        self.on_device = [f"{case}.perfetto-trace"]

    def shell(self, _command):
        return "\n".join(self.on_device)

    def pull(self, remote, local):
        Path(local).write_text(remote)


def test_pulling_after_each_case_keeps_every_trace_when_a_process_removes_the_earlier_ones(tmp_path):
    phone, into = Phone(), tmp_path / "traces"
    session = EnergySession(phone)
    for case in ("a", "b", "c"):
        phone.run_case(case)
        session.pull_traces(into, fresh=False)
    assert sorted(p.name for p in into.iterdir()) == ["a.perfetto-trace", "b.perfetto-trace", "c.perfetto-trace"]


def test_a_fresh_pull_starts_from_an_empty_folder(tmp_path):
    phone, into = Phone(), tmp_path / "traces"
    into.mkdir()
    (into / "old.perfetto-trace").write_text("x")
    phone.run_case("a")
    assert EnergySession(phone).pull_traces(into) == 1 and not (into / "old.perfetto-trace").exists()
