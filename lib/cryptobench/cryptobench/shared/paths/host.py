"""Locations in the user's home and on the host, read in one place."""
from __future__ import annotations

import os
from pathlib import Path

from .names import GLOBAL


def home() -> Path:
    return Path.home()


def _user_config() -> Path:
    return home() / ".config/cryptobench"


def user_global() -> Path:
    return _user_config() / GLOBAL


def user_devices() -> Path:
    """The user's device aliases; a fixed place, so an absent file is no aliases."""
    return _user_config() / "devices.yaml"


def user_cache() -> Path:
    """$XDG_CACHE_HOME/cryptobench, else ~/.cache/cryptobench."""
    return Path(os.environ.get("XDG_CACHE_HOME") or home() / ".cache") / "cryptobench"


def phone_lock(serial: str) -> Path:
    """The lock one run on this phone holds, whatever its results root."""
    return user_cache() / "locks" / serial


def android_home() -> Path:
    return Path(os.environ.get("ANDROID_HOME") or home() / "Library/Android/sdk")


def platform_tools() -> Path:
    return android_home() / "platform-tools"


def android_env() -> dict[str, str]:
    """This process's environment with ANDROID_HOME set, for a Gradle child that builds the Android modules."""
    return dict(os.environ, ANDROID_HOME=str(android_home()))
