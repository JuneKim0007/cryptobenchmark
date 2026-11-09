"""What a process may import beyond the installed library: the apps' source folders, for this process or a child."""
from __future__ import annotations

import os
import sys

from .repo import repo


def add_energy_imports() -> None:
    """The runner imports energy's capture rules and sources; appended, so the runner's own modules keep their names."""
    folder = str(repo().energy)
    if folder not in sys.path:
        sys.path.append(folder)


def add_app_imports() -> None:
    """The facade runs the runner's and perf-repair's code in one process."""
    r = repo()
    for folder in (r.runner, r.perf_repair_source):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))


def child_python_path(existing: str | None = None) -> str:
    """perf-repair's source for a child, ahead of what the environment already names."""
    return os.pathsep.join(p for p in (str(repo().perf_repair_source), existing) if p)
