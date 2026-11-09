"""Per-service lookups: each provider's services, the attributes a service declares, the key kind a generator makes."""
from __future__ import annotations

from typing import Callable, Iterator

from cryptobench.catalogue.names import Names

GENERATOR_KINDS = {"KeyGenerator": "secret", "KeyPairGenerator": "pair"}


def services(doc: dict) -> Iterator[tuple[dict, dict]]:
    return ((p, s) for p in doc.get("providers") or [] for s in p.get("services") or [])


def attributes_of(doc: dict) -> dict[tuple, dict]:
    return {(p["name"], s["type"], s["algorithm"]): s.get("attributes") or {} for p, s in services(doc)}


def class_names_of(doc: dict) -> dict[tuple, str | None]:
    return {(p["name"], s["type"], s["algorithm"]): s.get("className") for p, s in services(doc)}


def generator_kind(doc: dict, names: Names) -> Callable[[str], str | None]:
    keys = {(s["type"], names.key_or_spelling(s["type"], s["algorithm"]))
            for _, s in services(doc) if s["type"] in GENERATOR_KINDS}
    return lambda name: next((kind for engine, kind in GENERATOR_KINDS.items()
                              if (engine, names.key_or_spelling(engine, name)) in keys), None)
