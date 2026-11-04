"""<device>/.lock: one run on a device folder at a time; the process holding it may take it again without blocking."""
from __future__ import annotations

import fcntl
import os
from pathlib import Path

from ..dto.coded import InputError
from .layout import LOCK

# flock conflicts between two descriptors of one process too, so the guide and its probe_device share one
_HELD: dict[Path, list] = {}


class DeviceLock:

    def __init__(self, key: Path):
        self.key, self.held = key, True

    @classmethod
    def take(cls, folder: Path) -> DeviceLock:
        """device_busy when another process holds it; the descriptor is not inherited by children (O_CLOEXEC)."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        key = folder.resolve()
        if key in _HELD:
            _HELD[key][1] += 1
            return cls(key)
        fd = os.open(key / LOCK, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            owner = os.read(fd, 32).decode(errors="replace").strip() or "unknown"
            os.close(fd)
            raise InputError(f"device_busy: {folder} is in use by another run (pid {owner}); wait for it to end") from None
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode())
        _HELD[key] = [fd, 1]
        return cls(key)

    def release(self) -> None:
        if not self.held:
            return
        self.held = False
        held = _HELD[self.key]
        held[1] -= 1
        if not held[1]:
            del _HELD[self.key]
            os.close(held[0])

    def __enter__(self) -> DeviceLock:
        return self

    def __exit__(self, *_) -> None:
        self.release()
