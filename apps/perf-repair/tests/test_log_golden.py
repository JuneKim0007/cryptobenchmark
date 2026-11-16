"""One fake command run's events.jsonl, status.log and stderr against fixtures/log/golden_run.json; ts, run id and durations vary."""
import json
import logging
import re
import sys
from pathlib import Path

import pytest

from cryptobench.shared.log import attach as log_attach
from cryptobench.shared.log.emit import emit, step
from cryptobench.shared.log.event import DECISION
from cryptobench.shared.paths import RunTree
from cryptobench.shared.stop.terminate import terminate
from perfrepair import failure
from perfrepair.log import attach

GOLDEN = Path(__file__).parent / "fixtures" / "log" / "golden_run.json"
TIMED = ("end", "run_end")


@pytest.fixture
def logger():
    root = logging.getLogger("perfrepair")
    before, level = list(root.handlers), root.level
    root.handlers[:] = []
    yield root
    log_attach.SINK.close()
    root.handlers[:], root.level = before, level


def fake_run(folder: Path) -> int:
    attach()
    logging.getLogger("perfrepair.config.load").debug("setting a: 1 (default)")

    def body():
        attach(folder)
        logging.getLogger("perfrepair.inputs").info("an input line", extra={"code": "missing_input", "input": "a"})
        with step("grouping", "build", item="i1") as s:
            out = folder / "out.json"
            out.write_text("{}")
            s.count(items=2)
            s.wrote(out)
        emit("grouping", "assign", DECISION, kind="model", item="i1", outcome="dropped", durationMs=1200,
             tokens={"input": 10, "output": 2}, costUsd=0.001, ref="log/ai/grouping.yaml#1", data={"calls": 1})
        terminate("not_on_device", "P is not on the device", stage="device", step="s", item="P", app="a")
        raise ValueError("missing_file: x")
    return failure.reported(body)


def snapshot(folder: Path, err: str) -> dict:
    tree = RunTree(folder).log
    events = [json.loads(line) for line in tree.events.read_text().splitlines()]
    stamps = {e["run"]: "RUN" for e in events} | {e["ts"]: "TS" for e in events}

    def plain(text: str) -> str:
        for value, mark in stamps.items():
            text = text.replace(value, mark)
        return re.sub(r"\d+\.\ds\b", "Ns", text)
    for e in events:
        e["ts"], e["run"] = "TS", "RUN"
        if e["event"] in TIMED:
            e["durationMs"] = "MS"
    return {"events": events, "status": plain(tree.status.read_text()).splitlines(), "stderr": err}


def test_a_fake_run_writes_the_golden_events_status_and_stderr(tmp_path, logger, capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["/x/perfrepair/app/__main__.py", "--app", "a"])
    assert fake_run(tmp_path) == 1
    assert snapshot(tmp_path, capsys.readouterr().err) == json.loads(GOLDEN.read_text())
