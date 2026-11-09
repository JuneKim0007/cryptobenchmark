"""Locations in the user's home and on the host, read in one place."""
from __future__ import annotations

import os
from pathlib import Path

from .names import GLOBAL


def home() -> Path:
    return Path.home()


def user_global() -> Path:
    return home() / ".config/cryptobench" / GLOBAL


def android_home() -> Path:
    return Path(os.environ.get("ANDROID_HOME") or home() / "Library/Android/sdk")
