"""files.append_line after a crash cut a line, files.read_jsonl for its three readers, and the sink's own notices."""
import json
import logging

import pytest

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.files import append_line, read_jsonl
from perfrepair.log import attach, emit
from perfrepair.log import sink as sink_module
from perfrepair.log.attach import SINK
from perfrepair.log.read import Follower, read_events
from perfrepair.validation.events import validate_events

CUT_LINE = '{"schemaVersion": 1, "ts": "2026'


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield root
    SINK.close()
    root.handlers[:], root.level = before, level


def test_an_append_after_a_cut_line_writes_a_newline_first_and_reads_back(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text('{"n": 1}\n' + CUT_LINE)
    assert append_line(path, json.dumps({"n": 2})) and not append_line(path, json.dumps({"n": 3}))
    found = read_jsonl(path)
    assert found.records == [(1, {"n": 1}), (3, {"n": 2}), (4, {"n": 3})] and found.cut == [2]
    assert found.bad == [] and not found.partial


def test_a_line_that_is_no_cut_prefix_is_bad_not_skipped(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text('{"n": 1}\n{"n": 1}}\nnot json\n{"n": 2')
    found = read_jsonl(path)
    assert [n for n, _ in found.bad] == [2, 3] and found.records == [(1, {"n": 1})] and found.partial



def test_the_sink_repairs_a_cut_events_line_and_says_so(tmp_path, logger):
    attach()
    failure.reported(lambda: (attach(tmp_path), emit("x", "y", "end"))[1])
    events = tmp_path / rd.EVENTS
    events.write_text(events.read_text() + CUT_LINE)
    attach()
    failure.reported(lambda: (attach(tmp_path), emit("x", "z", "end"))[1])
    read = read_events(events)
    repaired = [e for e in read if e.data.get("code") == "append_repaired"]
    assert [e.data["file"] for e in repaired] == [rd.EVENTS] and [e.step for e in read if e.event == "end"] == ["y", "z"]
    assert validate_events(events) == [] and any(line.startswith("append_repaired run log: warn: ")
                                                for line in (tmp_path / rd.STATUS_LOG).read_text().splitlines())
    assert [e.step for e in Follower(events, from_start=True).poll() if e.event == "end"] == ["y", "z"]


def test_records_past_the_buffer_are_counted_in_one_log_dropped(tmp_path, logger, monkeypatch):
    monkeypatch.setattr(sink_module, "BUFFER_LIMIT", 3)
    attach()

    def body():
        for n in range(5):
            emit("x", f"s{n}", "end")
        attach(tmp_path)
    failure.reported(body)
    read = read_events(tmp_path / rd.EVENTS)
    [dropped] = [e for e in read if e.data.get("code") == "log_dropped"]
    assert dropped.data["dropped"] == 3 and [e.step for e in read if e.event == "end"] == ["s0", "s1"]


def test_an_unexpected_data_shape_keeps_its_event(tmp_path, logger):
    attach()
    failure.reported(lambda: (attach(tmp_path), emit("x", "y", "end", data={"files": ["a"], "when": object()}))[1])
    [end] = [e for e in read_events(tmp_path / rd.EVENTS) if e.event == "end"]
    assert end.data["files"] == ["a"] and end.data["when"].startswith("<object object")
