"""log/: events.jsonl through the sink, its views derived from the same events, run events and bug.log."""
import json
import logging

import pytest

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.dto.event import FIELDS, SCHEMA_VERSION, Event
from perfrepair.log import attach, emit, step
from perfrepair.log.attach import SINK
from perfrepair.log.read import read_events
from perfrepair.log.views import render


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield root
    SINK.close()
    root.handlers[:], root.level = before, level


def _run(folder, body):
    attach()
    return failure.reported(lambda: (attach(folder), body())[1])


def _lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_every_line_carries_every_field_of_the_schema(tmp_path, logger):
    _run(tmp_path, lambda: emit("grouping", "build", "end", outcome="ok", durationMs=3, data={"counts": {"items": 2}}))
    lines = _lines(tmp_path / rd.EVENTS)
    assert [e["event"] for e in lines] == ["run_start", "end", "run_end"]
    for line in lines:
        assert set(line) == set(FIELDS) and line["schemaVersion"] == SCHEMA_VERSION
        assert Event.from_json(line).to_json() == line
    assert len({e["run"] for e in lines}) == 1 and lines[-1]["outcome"] == "ok"


def test_records_before_the_folder_is_known_are_kept_in_order(tmp_path, logger):
    attach()
    logging.getLogger("perfrepair.config.load").debug("setting a: 1 (default)")

    def body():
        attach(tmp_path)
        logging.getLogger("perfrepair.inputs").info("after")

    failure.reported(body)
    lines = _lines(tmp_path / rd.EVENTS)
    assert [e["detail"] for e in lines if e["event"] == "log"] == ["setting a: 1 (default)", "after"]
    assert lines[0]["event"] == "run_start" and lines[1]["outcome"] == "debug" and lines[1]["stage"] == "config"


def test_a_missing_folder_is_never_created(tmp_path, logger):
    _run(tmp_path / "absent", lambda: emit("x", "y", "end"))
    assert not (tmp_path / "absent").exists()


def test_event_records_stay_off_stderr_and_log_lines_stay_on_it(tmp_path, logger, capsys):
    def body():
        emit("grouping", "build", "end", detail="not for stderr")
        logging.getLogger("perfrepair.inputs").info("for stderr")

    _run(tmp_path, body)
    assert capsys.readouterr().err == "for stderr\n"


def test_a_step_emits_start_and_end_with_counts_and_file_digests(tmp_path, logger):
    written = tmp_path / "out.json"

    def body():
        with step("grouping", "build") as s:
            written.write_text("{}")
            s.count(items=4)
            s.wrote(written)

    _run(tmp_path, body)
    end = [e for e in _lines(tmp_path / rd.EVENTS) if e["event"] == "end"][0]
    assert end["outcome"] == "ok" and end["durationMs"] >= 0
    assert end["data"] == {"counts": {"items": 4},
                           "files": {"out.json": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}}


def test_a_failing_step_ends_failed(tmp_path, logger):
    def body():
        with step("app", "detect"):
            raise ValueError("missing_file: x")

    assert _run(tmp_path, body) == 1
    ends = [e for e in _lines(tmp_path / rd.EVENTS) if e["event"] == "end"]
    assert ends[0]["outcome"] == "failed" and "missing_file" in ends[0]["detail"]


def _model_turns(tmp_path):
    def body():
        emit("grouping", "assign", "turn", kind="model", item="i1", outcome="rejected", durationMs=1200,
             tokens={"input": 10, "output": 2}, costUsd=0.001, ref=str(tmp_path / "grouping/journal.jsonl") + ":1",
             data={"session": 1, "turn": 1, "problems": ["gate: no such group"]})
        emit("screening", "classify", "turn", kind="model", item="b1", outcome="accepted", data={"session": 1, "turn": 1})
        emit("worthiness", "latency", "decision", kind="model", item="w1", outcome="decided")
        emit("replace", "site-replace", "turn", kind="model", item="u1", outcome="accepted")
        emit("grouping", "build", "end", outcome="ok")
    _run(tmp_path, body)


def test_each_view_is_the_render_of_the_events_it_was_written_from(tmp_path, logger):
    _model_turns(tmp_path)
    events = read_events(tmp_path / rd.EVENTS)
    for name, lines in render(events).items():
        path = tmp_path / name
        assert (path.read_text() if path.exists() else "") == "".join(line + "\n" for line in lines)
    grouping = (tmp_path / rd.AI_GROUPING_LOG).read_text()
    assert "i1" in grouping and "grouping/journal.jsonl:1" in grouping
    assert "no such group" in grouping and "b1" not in grouping
    assert "b1" in (tmp_path / rd.AI_CLASSIFY_LOG).read_text() and not (tmp_path / rd.AI_SCREENING_LOG).exists()
    assert "w1" in (tmp_path / rd.AI_WORTHINESS_LOG).read_text() and "u1" in (tmp_path / rd.AI_REPLACE_LOG).read_text()
    assert not (tmp_path / "log/grouping").exists() and not (tmp_path / "log/screening").exists()


def test_a_coded_error_is_no_bug(tmp_path, logger, capsys):
    def body():
        raise ValueError("missing_file: x")

    assert _run(tmp_path, body) == 1
    assert capsys.readouterr().err.startswith("error missing_file: ")
    assert not (tmp_path / rd.BUG_LOG).exists()
    lines = _lines(tmp_path / rd.EVENTS)
    assert [e["event"] for e in lines] == ["run_start", "error", "run_end"] and lines[-1]["outcome"] == "error"


def test_an_uncoded_exception_is_one_line_and_its_traceback_in_bug_log(tmp_path, logger, capsys):
    def body():
        raise KeyError("oops")

    assert _run(tmp_path, body) == 1
    err = capsys.readouterr().err
    assert err.startswith("error bug: ") and "Traceback" not in err
    bug = (tmp_path / rd.BUG_LOG).read_text()
    assert "KeyError: 'oops'" in bug and "Traceback (most recent call last)" in bug
    assert _lines(tmp_path / rd.EVENTS)[-1]["outcome"] == "bug"


def test_a_bug_before_the_folder_is_known_prints_its_traceback(logger, capsys):
    attach()
    assert failure.reported(lambda: {}["x"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error bug: KeyError: 'x'\nTraceback")


def test_a_command_called_by_another_joins_its_run(tmp_path, logger):
    def inner():
        attach()
        return failure.reported(lambda: emit("app", "detect", "end"))

    _run(tmp_path, inner)
    lines = _lines(tmp_path / rd.EVENTS)
    assert [e["event"] for e in lines] == ["run_start", "end", "run_end"] and len({e["run"] for e in lines}) == 1
