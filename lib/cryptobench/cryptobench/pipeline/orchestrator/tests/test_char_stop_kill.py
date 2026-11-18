"""Characterization (Py-P6): through shared/stop/child.py, a worker that ignores SIGTERM is SIGKILLed with its group once the stop grace has passed; the row reads stopped with
the exit -9 as its line."""
import io, sys

import pytest

from cryptobench.pipeline.orchestrator import run as session_run
from cryptobench.pipeline.orchestrator.board import StatusBoard
from cryptobench.shared.stop import child
from test_orchestrator import PIXEL, lines, session  # noqa: F401

DEAF = "import signal, sys, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nprint('deaf', flush=True)\ntime.sleep(60)\n"


def test_a_worker_deaf_to_sigterm_is_killed_after_the_grace(session, tmp_path, monkeypatch):  # noqa: F811
    script = tmp_path / "deaf_worker.py"
    script.write_text(DEAF)
    monkeypatch.setattr(child, "PIPELINE_GRACE_SECONDS", 0.5)
    real_sleep, polls = session_run.time.sleep, []

    def sleep(seconds):
        polls.append(seconds)
        if len(polls) == 3:
            raise KeyboardInterrupt
        real_sleep(seconds)
    monkeypatch.setattr(session_run.time, "sleep", sleep)
    (tmp_path / "session.yaml").write_text("schemaVersion: 1\nname: s\ndevices: {select: listed}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\n"
                                           "targets: {56301AAAA00001: {}}\n")
    with pytest.raises(KeyboardInterrupt):
        session_run.run_session(tmp_path / "session.yaml", tmp_path / "results", lambda: tmp_path / "global.yaml", [],
                                lambda *_arguments: [sys.executable, str(script)], StatusBoard(io.StringIO()))
    folder = tmp_path / "results/sessions/s"
    assert [line.split()[:4] for line in lines(folder / "summary.txt")[1:]] == [["56301AAAA00001", "tier1", "stopped", "subprocess_failed"]]
    assert any(line.endswith("stopped: 56301AAAA00001 tier1: subprocess_failed: pipeline.py exited -9") for line in lines(folder / "session.log"))
