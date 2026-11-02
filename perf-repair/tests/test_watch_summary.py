"""watch on a growing events.jsonl, and the summary's numbers on a scripted run."""
import io
import json

from helpers import QUIET
from test_engine import CHARTER, LabelKind
from test_engine_events import Billed

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.runtime.engine.events import Where
from perfrepair.dto.event import Event
from perfrepair.log import attach, step
from perfrepair.log.__main__ import main as log_main
from perfrepair.log.read import read_events
from perfrepair.log.summary import summarize
from perfrepair.log.watch import watch
from perfrepair.watch.__main__ import main as watch_main


def _scripted(tmp_path, limit=None):
    (tmp_path / "grouping").mkdir(parents=True, exist_ok=True)

    def body():
        attach(tmp_path)
        with step("grouping", "build") as s:
            s.count(items=3)
        decide(LabelKind(), CHARTER, Billed(), tmp_path / "grouping", where=Where("grouping", "assign"), limit=limit,
               **QUIET)

    attach()
    assert failure.reported(body) == 0
    return [json.dumps(e.to_json()) for e in read_events(tmp_path / rd.EVENTS)]


def test_watch_follows_a_growing_file_and_stops_at_the_run_end(tmp_path):
    lines = _scripted(tmp_path / "source")
    path = tmp_path / rd.EVENTS
    path.parent.mkdir(parents=True)
    pending = list(lines)

    def grow(_):
        # half a line first: the follower reads it only once it is whole
        chunk = pending.pop(0) + "\n" if pending else ""
        with path.open("a") as f:
            f.write(chunk[:10])
        with path.open("a") as f:
            f.write(chunk[10:])

    out = io.StringIO()
    assert watch(path, False, out, sleep=grow, polls=100) == 0
    printed = out.getvalue().splitlines()
    assert printed[0] == f"waiting for {path}" and printed[1].startswith("run ") and printed[1].endswith(": started")
    assert any(p.startswith("grouping build: ok items=3") for p in printed)
    counters = [p for p in printed if p.startswith("grouping assign ")]
    assert counters[0].startswith("grouping assign 0/3 · 0 rejected")
    assert "grouping assign 1/3 · 1 rejected · $0.0200" in "\n".join(counters)
    assert counters[-1].startswith("grouping assign 3/3 · 1 rejected · $0.0400") and counters[-1].endswith("· done")
    assert printed[-1].startswith("run ") and ": ok (" in printed[-1] and not pending


def test_watch_from_start_replays_a_finished_run_and_exits(tmp_path, capsys):
    _scripted(tmp_path)
    assert watch_main([str(tmp_path), "--from-start", "--interval", "0"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].endswith(": started") and out[-1].startswith("run ")


def test_on_a_terminal_a_counter_rewrites_its_line(tmp_path):
    _scripted(tmp_path)
    out = io.StringIO()
    assert watch(tmp_path / rd.EVENTS, True, out, tty=True, sleep=lambda _: None, polls=2) == 0
    text = out.getvalue()
    assert "\rgrouping assign 1/3" in text and "grouping assign 3/3 · 1 rejected · $0.0400" in text


def test_the_summary_counts_calls_rejections_tokens_cost_and_problems(tmp_path):
    _scripted(tmp_path)
    doc = summarize(read_events(tmp_path / rd.EVENTS))
    grouping = doc["stages"]["grouping"]
    assert doc["outcome"] == "ok" and doc["total"]["modelCalls"] == 4
    assert (grouping["items"], grouping["decisions"], grouping["modelCalls"], grouping["rejections"]) == (
        3, {"decided": 3}, 4, 1)
    assert grouping["tokens"] == {"input": 400, "output": 40, "cacheRead": 200, "cacheWrite": 0}
    assert grouping["costUsd"] == 0.04 and grouping["topProblems"] == [{"problem": "label is empty", "count": 1}]
    assert sorted((s["item"], s["turns"]) for s in grouping["slowest"]) == [("a", 2), ("b", 1), ("c", 1)]
    assert grouping["steps"]["build"]["runs"] == 1


def test_the_summary_is_of_the_last_run_unless_one_is_named(tmp_path, capsys):
    _scripted(tmp_path, limit=1)
    _scripted(tmp_path)
    events = read_events(tmp_path / rd.EVENTS)
    first, last = dict.fromkeys(e.run for e in events)
    assert summarize(events)["stages"]["grouping"]["items"] == 2
    assert summarize(events, first)["stages"]["grouping"]["modelCalls"] == 2
    assert log_main(["summary", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["run"] == last
    assert log_main(["summary", str(tmp_path)]) == 0
    text = capsys.readouterr().out
    assert f"run {last}" in text and "stage grouping:" in text and "2 model calls" in text


def test_a_summary_without_events_is_one_error_line(tmp_path, capsys):
    assert log_main(["summary", str(tmp_path)]) == 1
    assert capsys.readouterr().err.startswith("error missing_file: ")


def test_an_event_line_round_trips():
    e = Event("2026-11-03T00:00:00.000Z", "r", "grouping", "assign", "turn", "model", data={"session": 1})
    assert Event.from_json(json.loads(json.dumps(e.to_json()))) == e
