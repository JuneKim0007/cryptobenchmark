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


def platform_tools() -> Path:
    return android_home() / "platform-tools"


def android_env() -> dict[str, str]:
    """This process's environment with ANDROID_HOME set, for a Gradle child that builds the Android modules."""
    return dict(os.environ, ANDROID_HOME=str(android_home()))
