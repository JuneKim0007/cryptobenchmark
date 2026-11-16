"""files.read_jsonl for its three readers, and the sink's repair of a cut events line through the perf-repair views."""
import logging

import pytest

from cryptobench.shared.paths import RunTree
from cryptobench.shared.paths import EVENTS
from perfrepair import failure
from perfrepair.files import read_jsonl
from perfrepair.log import attach
from cryptobench.shared.log.emit import emit
from cryptobench.shared.log import attach as log_attach
from perfrepair.log.read import Follower, read_events
from perfrepair.validation.events import validate_events

CUT_LINE = '{"schemaVersion": 1, "ts": "2026'


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield root
    log_attach.SINK.close()
    root.handlers[:], root.level = before, level


def test_a_cut_line_is_skipped_and_the_lines_after_it_read(tmp_path):
    path = tmp_path / "a.jsonl"
    path.write_text('{"n": 1}\n' + CUT_LINE + '\n{"n": 2}\n{"n": 3}\n')
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
    events = RunTree(tmp_path).log.events
    events.write_text(events.read_text() + CUT_LINE)
    attach()
    failure.reported(lambda: (attach(tmp_path), emit("x", "z", "end"))[1])
    read = read_events(events)
    repaired = [e for e in read if e.data.get("code") == "append_repaired"]
    assert [e.data["file"] for e in repaired] == [EVENTS] and [e.step for e in read if e.event == "end"] == ["y", "z"]
    assert validate_events(events) == [] and any(line.startswith("append_repaired run log: warn: ")
                                                for line in (RunTree(tmp_path).log.status).read_text().splitlines())
    assert [e.step for e in Follower(events, from_start=True).poll() if e.event == "end"] == ["y", "z"]
