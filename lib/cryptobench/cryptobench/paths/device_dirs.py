"""Folders on an Android device, per API level; paired with DeviceDirectory.kt."""
from __future__ import annotations

from pathlib import PurePosixPath

PACKAGE = "io.github.junekim0007.cryptobench"
PLAN_DIRECTORY = "cryptobench"
SCOPE_KEYS = "scope-keys"
MEDIA_FROM_SDK = 29


class DeviceDirs:
    """Paths on the device stay POSIX whatever the host is."""

    def __init__(self, sdk: int):
        self.sdk = sdk

    @property
    def _app(self) -> PurePosixPath:
        return PurePosixPath(f"/sdcard/Android/{'media' if self.sdk >= MEDIA_FROM_SDK else 'data'}") / PACKAGE

    @property
    def plan(self) -> PurePosixPath:
        return (self._app if self.sdk >= MEDIA_FROM_SDK else self._app / "files") / PLAN_DIRECTORY

    @property
    def output(self) -> PurePosixPath:
        return self._app if self.sdk >= MEDIA_FROM_SDK else self._app / "cache"

    @property
    def scope_keys(self) -> PurePosixPath:
        return self.plan / SCOPE_KEYS
