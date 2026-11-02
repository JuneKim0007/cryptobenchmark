"""Per-service lookups: the attributes a service declares and the key kind a generator service makes."""
from __future__ import annotations

from typing import Callable

from ....catalog.names import Names

GENERATOR_KINDS = {"KeyGenerator": "secret", "KeyPairGenerator": "pair"}


def attributes_of(doc: dict) -> dict[tuple, dict]:
    return {(p["name"], s["type"], s["algorithm"]): s.get("attributes") or {}
            for p in doc["providers"] for s in p.get("services") or []}


def class_names_of(doc: dict) -> dict[tuple, str | None]:
    return {(p["name"], s["type"], s["algorithm"]): s.get("className")
            for p in doc["providers"] for s in p.get("services") or []}


def generator_kind(doc: dict, names: Names) -> Callable[[str], str | None]:
    keys = {(s["type"], names.canonical(s["type"], s["algorithm"]).key)
            for p in doc["providers"] for s in p.get("services") or [] if s["type"] in GENERATOR_KINDS}
    return lambda name: next((kind for engine, kind in GENERATOR_KINDS.items()
                              if (engine, names.canonical(engine, name).key) in keys), None)
