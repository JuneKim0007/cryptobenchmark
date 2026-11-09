"""What a path value in a settings file means, and whether a location is one the system may wipe."""
from __future__ import annotations

import tempfile
from pathlib import Path

TEMP_ROOTS = ("/tmp", "/var/tmp", "/var/folders")


def against(settings_file: Path | str, value: Path | str) -> Path:
    """A path value of a settings file: ~ expanded, joined to the file's folder, resolved."""
    return (Path(settings_file).parent / Path(str(value)).expanduser()).resolve()


def in_temp(path: Path | str) -> bool:
    real = Path(path).resolve()
    return any(real.is_relative_to(Path(root).resolve()) for root in (*TEMP_ROOTS, tempfile.gettempdir()))
