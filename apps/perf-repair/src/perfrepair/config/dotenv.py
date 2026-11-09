"""<perf-repair>/.env: its keys as a layer; keys outside PERFREPAIR_* also fill unset environment keys."""
from __future__ import annotations

import os
from pathlib import Path

from cryptobench import paths

ENV_FILE = paths.repo().dotenv
OWN_PREFIX = "PERFREPAIR_"


def read(path: Path | None = None) -> dict[str, str]:
    path = ENV_FILE if path is None else path
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if value:
            values[key] = value.strip("'\"")
    return values


def load_env(path: Path | None = None) -> dict[str, str]:
    values = read(path)
    for key, value in values.items():
        # PERFREPAIR_* stay out of os.environ: .env ranks below perfrepair.yaml, the real environment above it.
        if not key.startswith(OWN_PREFIX) and key not in os.environ:
            os.environ[key] = value
    return values
