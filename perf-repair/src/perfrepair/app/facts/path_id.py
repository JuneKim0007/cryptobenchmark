"""An app's id, the name of its folder under the device's: `<dirname>-<8 hex of sha256 of the absolute path>`."""
from __future__ import annotations

import re
from pathlib import Path

from ... import run_dir as rd
from ...files import read_json, sha256_text

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def absolute(path: Path | str) -> Path:
    return Path(path).expanduser().resolve()


def path_id(path: Path | str) -> str:
    real = absolute(path)
    return f"{_UNSAFE.sub('-', real.name).strip('.-_') or 'app'}-{sha256_text(str(real))[:8]}"


def unit_id(pid: str, project_root: str) -> str:
    return ".".join([pid, *project_root.split("/")])


def app_id(device: Path, path: Path | str) -> str:
    """The folder for --app: its own id, else the unit of a multi-root folder that recorded this path as its root."""
    own, real = path_id(path), str(absolute(path))
    if not (Path(device) / own).is_dir():
        for folder in rd.app_dirs(device):
            if read_json(folder / rd.APP)["root"] == real:
                return folder.name
    return own
