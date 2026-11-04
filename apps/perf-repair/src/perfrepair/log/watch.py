"""watch(): follows events.jsonl by polling and prints Progress lines until a run ends."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, TextIO

from ..dto.event import RUN_END
from .progress import Line, Progress
from .read import Follower


class Screen:
    """On a terminal a counter overwrites itself; elsewhere every line is kept."""

    def __init__(self, out: TextIO, tty: bool):
        self.out, self.tty, self.open = out, tty, False

    def show(self, line: Line) -> None:
        if line.minor and not self.tty:
            return
        if self.tty and line.transient:
            self.out.write("\r" + line.text + "\x1b[K")
            self.open = True
        else:
            self.out.write(("\r\x1b[K" if self.open else "") + line.text + "\n")
            self.open = False
        self.out.flush()

    def close(self) -> None:
        if self.open:
            self.out.write("\n")
            self.open = False


def watch(path: Path, from_start: bool, out: TextIO, tty: bool = False, interval: float = 0.5,
          sleep: Callable[[float], None] = time.sleep, polls: int | None = None) -> int:
    """Exits 0 once the last event read is a run's end; polls bounds the loop for tests."""
    follower, progress, screen = Follower(path, from_start), Progress(), Screen(out, tty)
    if not Path(path).is_file():
        screen.show(Line(f"waiting for {path}"))
    n = 0
    while polls is None or n < polls:
        events = follower.poll()
        for e in events:
            for line in progress.feed(e):
                screen.show(line)
        if events and events[-1].event == RUN_END:
            screen.close()
            return 0
        n += 1
        sleep(interval)
    screen.close()
    return 1
