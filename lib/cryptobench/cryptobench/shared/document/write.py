"""write_text: a file replaced whole by renaming a temporary of its writer's own over it, so a reader sees the old file or the
whole new one; write_texts stages every file before the first rename."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

TEMP_SUFFIX = ".tmp"
# mkstemp makes 0600; a staged file keeps the mode a plain open would give
_UMASK = os.umask(0)
os.umask(_UMASK)


@dataclass(frozen=True)
class Staging:
    """The temporary's name around the file's (`<prefix><name>.XXXX<suffix>`); private keeps mkstemp's 0600; synced fsyncs it
    even when the write is not durable."""
    prefix: str = ""
    suffix: str = TEMP_SUFFIX
    private: bool = False
    synced: bool = False


STAGED = Staging()
# the runner's manifest.yaml as it has always been written: a hidden temporary, 0600, fsync'd (C17 changes the mode in 1-C)
MANIFEST = Staging(prefix=".", suffix="", private=True, synced=True)


def _staged(path: Path, text: str, durable: bool, staging: Staging) -> Path:
    # a name of its own per writer: a shared `<name>.tmp` let two writers rename each other's file away (#78)
    handle, name = tempfile.mkstemp(prefix=f"{staging.prefix}{path.name}.", suffix=staging.suffix, dir=path.parent)
    tmp = Path(name)
    try:
        if not staging.private:
            os.fchmod(handle, 0o666 & ~_UMASK)
        with os.fdopen(handle, "w") as f:
            f.write(text)
            if durable or staging.synced:
                f.flush()
                os.fsync(f.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return tmp


def write_texts(texts: list[tuple[Path, str]]) -> None:
    """Every file is staged before the first rename, so a failure while staging leaves every old file; renames run in order."""
    staged = [(_staged(Path(p), t, False, STAGED), Path(p)) for p, t in texts]
    for tmp, path in staged:
        os.replace(tmp, path)


def write_text(path: Path, text: str, durable: bool = False, exclusive: bool = False, staging: Staging = STAGED) -> Path:
    """durable: the file and its folder are fsync'd; exclusive: an existing file is refused, checked before staging."""
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(f"{path}: already written")
    tmp = _staged(path, text, durable, staging)
    try:
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    if durable:
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    return path
