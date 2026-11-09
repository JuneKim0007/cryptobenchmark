"""log/ai/<job>.yaml: one entry per attempt of a job, appended, never rewritten; opened at the job's start even when it
asks nothing; each entry also goes out as one event (its ref the entry) and one TTY line."""
from __future__ import annotations

from pathlib import Path

import yaml

from cryptobench.catalogue.document import DocumentKind
from ...dto.event import DECISION
from ...files import append_line, write_text_making_parents
from ...log import emit, run_id
from ...run_dir import ai_log
from .where import Where

SCHEMA_VERSION = 1
# a turn the gate did not take
REJECTED = ("rejected", "refused")
ATTEMPT_LOG_DOC = DocumentKind("attempt log", SCHEMA_VERSION)
ATTEMPTS = "attempts:"


class AttemptLog:

    def __init__(self, device: Path, job: str, where: Where, echo=print):
        self.device, self.job, self.where, self.echo = Path(device), job, where, echo
        self.path = ai_log(device, job)
        self.count: int | None = None

    def open(self) -> "AttemptLog":
        """Writes the header of an empty log, or counts what earlier runs logged; called by the job template first."""
        if self.count is None:
            text = self.path.read_text() if self.path.is_file() else ""
            if not _appendable(text):
                # a missing log, or one written whole by an earlier version: its attempts once into the appending form
                found = read_log(self.path)["attempts"] if text.strip() else []
                write_text_making_parents(self.path, _header(self.job) + "".join(_item(a) for a in found))
                text = self.path.read_text()
            # an entry is a top-level sequence item; every other line of it is indented
            self.count = sum(line.startswith("- ") for line in text.splitlines())
        return self

    def append(self, entry: dict) -> int:
        """One entry appended as its own sequence item under attempts; nothing before it is rewritten."""
        n = self.open().count + 1
        append_line(self.path, _item({"n": n, "run": run_id(), "app": self.where.app, **entry}))
        self.count = n
        w, line, turns = self.where, _line(self.job, entry), entry.get("turns") or ()
        # the event points at its entry and carries only the counts the run summary adds up
        emit(w.stage, w.step, DECISION, kind="model", item=entry.get("item"), app=w.app, outcome=entry.get("outcome"),
             durationMs=entry.get("durationMs"), tokens=entry.get("tokens"), costUsd=entry.get("costUsd"),
             ref=f"{self.path.relative_to(self.device)}#{n}", detail=line,
             data={"label": entry.get("label"), "attempt": entry.get("attempt"), "calls": len(turns),
                   "rejected": sum(t.get("status") in REJECTED for t in turns),
                   "problems": [p for t in turns for p in t.get("problems") or ()]})
        self.echo(line)
        return n


def _header(job: str) -> str:
    return yaml.safe_dump({"schemaVersion": SCHEMA_VERSION, "job": job}, sort_keys=False) + f"{ATTEMPTS}\n"


def _item(entry: dict) -> str:
    return yaml.safe_dump([entry], sort_keys=False, allow_unicode=True)


def _appendable(text: str) -> bool:
    """attempts is the last key, as a block sequence an appended item extends."""
    lines = text.splitlines()
    if ATTEMPTS not in lines:
        return False
    return all(line.startswith(("- ", "  ")) for line in lines[lines.index(ATTEMPTS) + 1:])


def read_log(path: Path) -> dict:
    """log/ai/<job>.yaml with its attempts, an empty list before the first."""
    doc = ATTEMPT_LOG_DOC.read(path)
    return {**doc, "attempts": doc.get("attempts") or []}


def _line(job: str, e: dict) -> str:
    used = e.get("tokens") or {}
    spent = f" tokens {used.get('input', 0)}/{used.get('output', 0)}" if used else ""
    why = f": {e['reason']['source']}: {'; '.join(e['reason']['problems'])[:200]}" if e.get("reason") else ""
    return f"{job} {e.get('label') or e.get('item')}: {e.get('outcome')} [attempt {e.get('attempt')}, {e.get('tier', {}).get('model')}]{spent}{why}"
