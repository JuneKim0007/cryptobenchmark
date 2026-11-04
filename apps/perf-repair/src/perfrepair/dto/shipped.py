"""The providers an app ships, read from app.json `bundled`."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shipped:
    artifact: str
    providerName: str | None
    version: str | None = None


def shipped(app_doc: dict) -> tuple[Shipped, ...]:
    return tuple(Shipped(b["artifact"], b.get("providerName"), b.get("version")) for b in app_doc.get("bundled") or [])


def shipped_names(app_doc: dict) -> set[str]:
    return {s.providerName for s in shipped(app_doc) if s.providerName}
