"""StatusBoard: one status line per target the orchestrator renders; redrawn in place on a terminal, else printed when a line changes."""
from __future__ import annotations

import sys

WIDTH = 160


class StatusBoard:

    def __init__(self, stream=None):
        self.stream = stream or sys.stdout
        self.lines: dict[str, str] = {}
        self.drawn = 0
        self.live = self.stream.isatty()

    def update(self, target: str, status: str) -> None:
        line = f"target:    {target}: {status}"[:WIDTH]
        if self.lines.get(target) == line:
            return
        self.lines[target] = line
        if self.live:
            self.render()
        else:
            print(line, file=self.stream, flush=True)

    def render(self) -> None:
        up = f"\x1b[{self.drawn}F" if self.drawn else ""
        self.stream.write(up + "".join(f"\x1b[2K{line}\n" for line in self.lines.values()))
        self.stream.flush()
        self.drawn = len(self.lines)

    def done(self) -> None:
        """Lines printed after this start below the board."""
        self.drawn = 0
