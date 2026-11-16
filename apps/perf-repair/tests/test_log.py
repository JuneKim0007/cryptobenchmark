"""log/: perf-repair's views derived from the events they were written from, coded errors and bug.log."""
import json
import logging

import pytest

from cryptobench.shared.paths import RunTree
from cryptobench.shared.paths import AI_LOGS
from perfrepair import failure
from perfrepair.log import attach
from cryptobench.shared.log.emit import emit
from cryptobench.shared.log import attach as log_attach
from perfrepair.log.read import read_events
from perfrepair.log.views import render


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield root
    log_attach.SINK.close()
    root.handlers[:], root.level = before, level


def _run(folder, body):
    attach()
    return failure.reported(lambda: (attach(folder), body())[1])


def _lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def _model_turns(tmp_path):
    def body():
        emit("grouping", "assign", "decision", kind="model", item="i1", outcome="dropped", durationMs=1200,
             tokens={"input": 10, "output": 2}, costUsd=0.001, ref="log/ai/grouping.yaml#1",
             data={"calls": 1, "rejected": 1, "problems": ["gate: no such group"]})
        emit("grouping", "build", "end", outcome="ok")
    _run(tmp_path, body)


def test_each_view_is_the_render_of_the_events_it_was_written_from(tmp_path, logger):
    _model_turns(tmp_path)
    events = read_events(RunTree(tmp_path).log.events)
    for name, lines in render(events).items():
        path = tmp_path / name
        assert (path.read_text() if path.exists() else "") == "".join(line + "\n" for line in lines)
    # the attempt log is the AI view: no view of events copies it
    assert not (tmp_path / AI_LOGS).exists() and not (tmp_path / "log/grouping").exists()


def test_a_coded_error_is_no_bug(tmp_path, logger, capsys):
    def body():
        raise ValueError("missing_file: x")

    assert _run(tmp_path, body) == 1
    assert capsys.readouterr().err.startswith("error missing_file: ")
    assert not (RunTree(tmp_path).log.bug).exists()
    lines = _lines(RunTree(tmp_path).log.events)
    assert [e["event"] for e in lines] == ["run_start", "error", "run_end"] and lines[-1]["outcome"] == "error"


def test_an_uncoded_exception_is_one_line_and_its_traceback_in_bug_log(tmp_path, logger, capsys):
    def body():
        raise KeyError("oops")

    assert _run(tmp_path, body) == 1
    err = capsys.readouterr().err
    assert err.startswith("error bug: ") and "Traceback" not in err
    bug = (RunTree(tmp_path).log.bug).read_text()
    assert "KeyError: 'oops'" in bug and "Traceback (most recent call last)" in bug
    assert _lines(RunTree(tmp_path).log.events)[-1]["outcome"] == "bug"


def test_a_bug_before_the_folder_is_known_prints_its_traceback(logger, capsys):
    attach()
    assert failure.reported(lambda: {}["x"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error bug: KeyError: 'x'\nTraceback")
