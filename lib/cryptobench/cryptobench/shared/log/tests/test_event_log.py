"""cryptobench.shared.log: append_line, and events.jsonl through attach and the sink under a root logger of no views."""
import json
import logging

import pytest

from cryptobench.shared.document.append import append_line
from cryptobench.shared.log import attach as log_attach
from cryptobench.shared.log import sink as sink_module
from cryptobench.shared.log.attach import attach, command_run
from cryptobench.shared.log.emit import LOGGER, emit, step
from cryptobench.shared.log.event import FIELDS, SCHEMA_VERSION, Event
from cryptobench.shared.paths import RunTree

ROOT = "logtest"
CUT_LINE = '{"schemaVersion": 1, "ts": "2026'


@pytest.fixture(autouse=True)
def logger():
    loggers = [logging.getLogger(ROOT), LOGGER]
    kept = [(list(lg.handlers), lg.level) for lg in loggers]
    for lg in loggers:
        lg.handlers[:] = []
    yield loggers[0]
    log_attach.SINK.close()
    for lg, (handlers, level) in zip(loggers, kept):
        lg.handlers[:], lg.level = handlers, level


def _run(folder, body, outcome="ok"):
    attach(ROOT, ())
    with command_run() as run:
        attach(ROOT, (), folder)
        body()
        run.outcome = outcome


def _lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_an_append_after_a_cut_line_writes_a_newline_first(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text('{"n": 1}\n' + CUT_LINE)
    assert append_line(path, json.dumps({"n": 2})) and not append_line(path, json.dumps({"n": 3}))
    assert path.read_text() == '{"n": 1}\n' + CUT_LINE + '\n{"n": 2}\n{"n": 3}\n'


def test_every_line_carries_every_field_of_the_schema(tmp_path):
    _run(tmp_path, lambda: emit("grouping", "build", "end", outcome="ok", durationMs=3, data={"counts": {"items": 2}}))
    lines = _lines(RunTree(tmp_path).log.events)
    assert [e["event"] for e in lines] == ["run_start", "end", "run_end"]
    for line in lines:
        assert set(line) == set(FIELDS) and line["schemaVersion"] == SCHEMA_VERSION
        assert Event.from_json(line).to_json() == line
    assert len({e["run"] for e in lines}) == 1 and lines[-1]["outcome"] == "ok"


def test_records_before_the_folder_is_known_are_kept_in_order(tmp_path):
    attach(ROOT, ())
    logging.getLogger(f"{ROOT}.config.load").debug("setting a: 1 (default)")
    with command_run():
        attach(ROOT, (), tmp_path)
        logging.getLogger(f"{ROOT}.inputs").info("after")
    lines = _lines(RunTree(tmp_path).log.events)
    assert [e["detail"] for e in lines if e["event"] == "log"] == ["setting a: 1 (default)", "after"]
    assert lines[0]["event"] == "run_start" and lines[1]["outcome"] == "debug" and lines[1]["stage"] == "config"


def test_a_missing_folder_is_never_created(tmp_path):
    _run(tmp_path / "absent", lambda: emit("x", "y", "end"))
    assert not (tmp_path / "absent").exists()


def test_event_records_stay_off_stderr_and_log_lines_stay_on_it(tmp_path, capsys):
    def body():
        emit("grouping", "build", "end", detail="not for stderr")
        logging.getLogger(f"{ROOT}.inputs").info("for stderr")

    _run(tmp_path, body)
    assert capsys.readouterr().err == "for stderr\n"


def test_a_step_emits_start_and_end_with_counts_and_file_digests(tmp_path):
    written = tmp_path / "out.json"

    def body():
        with step("grouping", "build") as s:
            written.write_text("{}")
            s.count(items=4)
            s.wrote(written)

    _run(tmp_path, body)
    end = [e for e in _lines(RunTree(tmp_path).log.events) if e["event"] == "end"][0]
    assert end["outcome"] == "ok" and end["durationMs"] >= 0
    assert end["data"] == {"counts": {"items": 4},
                           "files": {"out.json": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}}


def test_a_failing_step_ends_failed(tmp_path):
    def body():
        with step("app", "detect"):
            raise ValueError("missing_file: x")

    with pytest.raises(ValueError):
        _run(tmp_path, body)
    lines = _lines(RunTree(tmp_path).log.events)
    ends = [e for e in lines if e["event"] == "end"]
    assert ends[0]["outcome"] == "failed" and "missing_file" in ends[0]["detail"] and lines[-1]["outcome"] == "failed"


def test_a_command_called_by_another_joins_its_run(tmp_path):
    def inner():
        attach(ROOT, ())
        with command_run():
            emit("app", "detect", "end")

    _run(tmp_path, inner)
    lines = _lines(RunTree(tmp_path).log.events)
    assert [e["event"] for e in lines] == ["run_start", "end", "run_end"] and len({e["run"] for e in lines}) == 1


def test_records_past_the_buffer_are_counted_in_one_log_dropped(tmp_path, monkeypatch):
    monkeypatch.setattr(sink_module, "BUFFER_LIMIT", 3)
    attach(ROOT, ())
    with command_run():
        for n in range(5):
            emit("x", f"s{n}", "end")
        attach(ROOT, (), tmp_path)
    lines = _lines(RunTree(tmp_path).log.events)
    [dropped] = [e for e in lines if e["data"].get("code") == "log_dropped"]
    assert dropped["data"]["dropped"] == 3 and [e["step"] for e in lines if e["event"] == "end"] == ["s0", "s1"]


def test_an_unexpected_data_shape_keeps_its_event(tmp_path):
    _run(tmp_path, lambda: emit("x", "y", "end", data={"files": ["a"], "when": object()}))
    [end] = [e for e in _lines(RunTree(tmp_path).log.events) if e["event"] == "end"]
    assert end["data"]["files"] == ["a"] and end["data"]["when"].startswith("<object object")


def test_each_view_appends_its_line_beside_events_jsonl(tmp_path):
    _run(tmp_path, lambda: emit("x", "y", "end"), outcome="ok")
    attach(ROOT, (("ends.log", lambda e: e.step if e.event == "end" else None),))
    with command_run():
        attach(ROOT, log_attach.SINK.views, tmp_path)
        emit("x", "z", "end")
    assert (tmp_path / "ends.log").read_text() == "z\n"
