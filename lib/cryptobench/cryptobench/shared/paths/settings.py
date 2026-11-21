"""What a path value in a settings file means (Python's rule, and Kotlin's for the authored test set), and whether a location is one the system may wipe."""
from __future__ import annotations

import tempfile
from pathlib import Path

TEMP_ROOTS = ("/tmp", "/var/tmp", "/var/folders")


def against(settings_file: Path | str, value: Path | str) -> Path:
    """A path value of a settings file: ~ expanded, joined to the file's folder, resolved."""
    return (Path(settings_file).parent / Path(str(value)).expanduser()).resolve()


def beside(settings_file: Path | str, value: Path | str) -> Path:
    """Kotlin Beside.authored: an absolute value stands, else it joins the file's absolute folder; no ~, nothing resolved."""
    named = Path(str(value))
    return named if named.is_absolute() else Path(settings_file).absolute().parent / named


def in_temp(path: Path | str) -> bool:
    real = Path(path).resolve()
    return any(real.is_relative_to(Path(root).resolve()) for root in (*TEMP_ROOTS, tempfile.gettempdir()))
