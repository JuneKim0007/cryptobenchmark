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


def with_app_imports(env: dict[str, str]) -> dict[str, str]:
    """A child's environment with perf-repair's source on its import path, ahead of what the environment already names."""
    existing = env.get("PYTHONPATH")
    return {**env, "PYTHONPATH": os.pathsep.join(p for p in (str(repo().perf_repair_source), existing) if p)}
