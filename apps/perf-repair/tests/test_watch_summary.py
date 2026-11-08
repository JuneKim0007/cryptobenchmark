"""watch on a growing events.jsonl, and the summary's numbers on a scripted run."""
import io
import json

from helpers import QUIET
from test_engine import CHARTER, LabelKind
from test_engine_events import Billed

from perfrepair import failure
from perfrepair import run_dir as rd
from perfrepair.ai.runtime.engine.decide import decide
from perfrepair.ai.log.where import Where
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
    counters = [p for p in printed if p.startswith("grouping assign ")]
    assert "0/3" in counters[0] and "3/3" in counters[-1] and "$0.0400" in counters[-1]
    assert ": ok (" in printed[-1] and not pending


def test_watch_from_start_replays_a_finished_run_and_exits(tmp_path, capsys):
    _scripted(tmp_path)
    assert watch_main([str(tmp_path), "--from-start", "--interval", "0"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert "started" in out[0] and "ok" in out[-1]


def test_on_a_terminal_a_counter_rewrites_its_line(tmp_path):
    _scripted(tmp_path)
    out = io.StringIO()
    assert watch(tmp_path / rd.EVENTS, True, out, tty=True, sleep=lambda _: None, polls=2) == 0
    text = out.getvalue()
    assert "\rgrouping assign 1/3" in text


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


def test_the_summary_is_of_every_run_unless_narrowed(tmp_path, capsys):
    _scripted(tmp_path, limit=1)
    _scripted(tmp_path)
    events = read_events(tmp_path / rd.EVENTS)
    first, last = dict.fromkeys(e.run for e in events)
    every = summarize(events)
    assert every["run"] == "all" and every["total"]["modelCalls"] == 4 and every["total"]["costUsd"] == 0.04
    assert every["stages"]["grouping"]["items"] == 3 and [r["run"] for r in every["runs"]] == [first, last]
    assert every["durationMs"] == sum(r["durationMs"] for r in every["runs"]) and every["outcome"] == "ok 2"
    assert summarize(events, first)["stages"]["grouping"]["modelCalls"] == 2
    assert summarize(events, last=True)["stages"]["grouping"]["items"] == 2
    assert log_main(["summary", str(tmp_path), "--json", "--last"]) == 0
    assert json.loads(capsys.readouterr().out)["run"] == last
    assert log_main(["summary", str(tmp_path)]) == 0
    text = capsys.readouterr().out
    assert first in text and last in text


def test_the_summary_ends_with_the_status_lines_of_the_runs_it_shows(tmp_path, capsys):
    _scripted(tmp_path, limit=1)
    _scripted(tmp_path)
    events = read_events(tmp_path / rd.EVENTS)
    first, last = dict.fromkeys(e.run for e in events)
    assert summarize(events, last=True)["status"] == (tmp_path / rd.STATUS_LOG).read_text().splitlines()[2:]
    assert log_main(["summary", str(tmp_path), "--last"]) == 0
    text = capsys.readouterr().out.splitlines()
    status = text[text.index("status:") + 1:]
    assert last in status[0] and last in status[-1] and not any(first in line for line in status)


def test_a_run_with_no_end_is_running_if_newest_and_else_unfinished(tmp_path):
    _scripted(tmp_path, limit=1)
    _scripted(tmp_path)
    path = tmp_path / rd.EVENTS
    path.write_text("".join(line + "\n" for line in path.read_text().splitlines() if '"run_end"' not in line))
    every = summarize(read_events(path))
    assert [r["outcome"] for r in every["runs"]] == ["unfinished", "running"]
    assert every["outcome"] == "running 1, unfinished 1"


def test_a_killed_model_step_still_counts_its_turns_as_time(tmp_path):
    _scripted(tmp_path)
    path = tmp_path / rd.EVENTS
    lines = [line for line in path.read_text().splitlines() if not ('"end"' in line and '"assign"' in line)]
    path.write_text("".join(line + "\n" for line in lines))
    events = read_events(path)
    turns = sum(e.durationMs or 0 for e in events if e.event == "turn")
    built = sum(e.durationMs or 0 for e in events if e.event == "end" and e.step == "build")
    assert summarize(events)["stages"]["grouping"]["durationMs"] == turns + built


def test_a_report_after_paid_runs_does_not_hide_them(tmp_path, capsys):
    _scripted(tmp_path)

    def report_only():
        attach(tmp_path)
        with step("report", "summary"):
            pass

    attach()
    assert failure.reported(report_only) == 0
    assert log_main(["summary", str(tmp_path)]) == 0
    assert "$0.0400" in capsys.readouterr().out


def test_a_summary_without_events_is_one_error_line(tmp_path, capsys):
    assert log_main(["summary", str(tmp_path)]) == 1
    assert capsys.readouterr().err.startswith("error missing_file: ")


def test_a_run_start_drops_a_counter_a_killed_run_left_open():
    from perfrepair.log.progress import Progress
    progress = Progress()

    def ev(event, kind="model", **kw):
        return Event("2026-11-03T00:00:00.000Z", "r", "grouping", "review", event, kind, **kw)

    progress.feed(ev("start", data={"pending": 2}))
    progress.feed(ev("decision", outcome="reviewed"))
    progress.feed(ev("run_start", kind="static"))
    assert progress.feed(ev("decision", outcome="reviewed"))[0].text.startswith("grouping review 1/1 ")
