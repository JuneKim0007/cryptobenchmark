"""The status view: one line per outcome a person acts on, each starting with its code word, a header per run."""
from __future__ import annotations

import re
from typing import Callable

from ..dto.event import BUG, END, ERROR, FINDING, RUN_END, RUN_START, Event
from ..run_dir import BUG_LOG

# a code holds an underscore, or is one word before a colon: prose such as "pipeline exited 1" is none
CODE = re.compile(r"^(?:([a-z][a-z0-9]*_[a-z0-9_]+)\b|([a-z]+):)")
DEVICE_OUTCOMES = ("ran", "reused", "failed")
AT_STEP = re.compile(r"^at (\S+): ")
# a first line ending in a clause that introduces the lines below it (`; last lines:`)
LEADS_IN = re.compile(r";[^;]*:$")


def first_line(text: str) -> str:
    return LEADS_IN.sub("", (text or "").split("\n", 1)[0].strip())


def code_of(text: str, fallback: str) -> str:
    """The code word a detail starts with (`no_options: ...`, `missing_device_stage ...`), else fallback."""
    found = CODE.match(first_line(text))
    return (found.group(1) or found.group(2)) if found else fallback


def after_code(text: str, code: str) -> str:
    line = first_line(text)
    return line[len(code):].lstrip(": ") if line.startswith(code) else line


def line(code: str, subject: str, detail: str = "") -> str:
    return f"{code} {subject}" + (f": {detail}" if detail else "")


def _seconds(ms: int | None) -> str:
    return "" if ms is None else f" ({ms / 1000:.1f}s)"


def _run_start(e: Event) -> str:
    return line("run", f"{e.run} {e.ts}", e.detail or e.step)


def _run_end(e: Event) -> str:
    return line("end", e.run, f"{e.outcome}{_seconds(e.durationMs)}")


def last_error(text: str) -> str:
    errors = [s.strip() for s in (text or "").splitlines()[1:] if s.strip().startswith("error")]
    return f"; last {errors[-1]}" if errors else ""


def _target(e: Event) -> str:
    code = e.data.get("code") or (code_of(e.detail, e.outcome) if e.outcome == "stop" else e.outcome)
    rest = after_code(e.detail, code)
    at = AT_STEP.match(rest)
    subject = f"app {e.app}" + (f" at {at.group(1)}" if at else "")
    return line(code, subject, (rest[at.end():] if at else rest) + last_error(e.detail))


def _guide_stop(e: Event) -> str:
    code = code_of(e.detail, e.outcome)
    return line(code, f"guide {e.step}", after_code(e.detail, code) + last_error(e.detail))


def _device(e: Event) -> str:
    code = code_of(e.detail.split(": ", 1)[-1], e.outcome) if e.outcome == "failed" else e.outcome
    return line(code, f"device {e.step}", first_line(e.detail) + last_error(e.detail))


def _finding(e: Event) -> str:
    subject = " ".join(p for p in (e.item or e.step, f"app {e.app}" if e.app else "") if p)
    return line(e.outcome or e.step, subject, first_line(e.detail) + (f"; see {e.ref}" if e.ref else ""))


def _error(e: Event) -> str:
    code = code_of(e.detail, "error")
    return line(code, "error", after_code(e.detail, code))


def _bug(e: Event) -> str:
    return line("bug", f"{e.stage} {e.step}", f"{first_line(e.detail)}; traceback in {BUG_LOG}")


def _kind(e: Event) -> Callable[[Event], str] | None:
    if e.event == END and e.kind == "static":
        if e.stage == "guide" and e.step == "target":
            return _target
        if e.stage == "guide" and e.app is None and e.outcome == "stop":
            return _guide_stop
        if e.stage == "device" and e.outcome in DEVICE_OUTCOMES:
            return _device
        return None
    return {RUN_START: _run_start, RUN_END: _run_end, FINDING: _finding, ERROR: _error, BUG: _bug}.get(e.event)


def status_line(e: Event) -> str | None:
    kind = _kind(e)
    return None if kind is None else kind(e)
