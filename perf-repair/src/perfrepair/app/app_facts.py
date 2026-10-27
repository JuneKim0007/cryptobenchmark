"""The app.json document: bundled crypto libraries, provider registrations, SDK levels."""
from __future__ import annotations

from pathlib import Path

from .dependencies import Bundled, Registration

SCHEMA_VERSION = 1


def app_facts(app: str, root: Path, bundled: list[Bundled], registers: list[Registration],
              sdk: dict[str, int | None]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "app": app, "root": str(root),
            "bundled": [{"artifact": b.artifact, "providerName": b.providerName} for b in bundled],
            "registers": [r.to_json() for r in registers],
            "minSdk": sdk["minSdk"], "targetSdk": sdk["targetSdk"]}
