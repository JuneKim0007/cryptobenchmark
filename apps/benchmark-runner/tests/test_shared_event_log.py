"""The runner can attach the library's event log: step() and terminate() write events.jsonl in a temporary device folder."""
import json
import logging

import pytest

from cryptobench.shared.log import attach as log_attach
from cryptobench.shared.log.attach import attach, command_run
from cryptobench.shared.log.emit import LOGGER, step
from cryptobench.shared.paths import RunTree
from cryptobench.shared.stop.codes import CODES_LIST
from cryptobench.shared.stop.terminate import terminate

ROOT = "runner"


@pytest.fixture
def loggers():
    found = [logging.getLogger(ROOT), LOGGER]
    kept = [(list(lg.handlers), lg.level) for lg in found]
    yield
    log_attach.SINK.close()
    for lg, (handlers, level) in zip(found, kept):
        lg.handlers[:], lg.level = handlers, level


def test_the_runner_attaches_the_sink_and_step_and_terminate_write_events_jsonl(tmp_path, loggers):
    warn = next(c.code for c in CODES_LIST if c.action == "warn")
    attach(ROOT, ())
    with command_run() as run:
        attach(ROOT, (), tmp_path)
        with step("benchmark", "session") as s:
            s.count(cases=2)
        assert terminate(warn, "d", stage="benchmark", step="session") == "warn"
        run.outcome = "ok"
    lines = [json.loads(line) for line in RunTree(tmp_path).log.events.read_text().splitlines()]
    assert [(e["step"], e["event"]) for e in lines[1:-1]] == [("session", "start"), ("session", "end"),
                                                             ("session", "finding")]
    assert lines[0]["event"] == "run_start" and lines[-1]["outcome"] == "ok" and lines[2]["data"] == {"counts": {"cases": 2}}
    assert lines[3]["data"]["code"] == warn and len({e["run"] for e in lines}) == 1
