from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cryptobench.catalogue.names import Names
from cryptobench.catalogue.families import Families

SECRET, PAIR, UNKNOWN = "secret", "pair", "unknown"
FROM_CATALOGUE = "catalogue"


@dataclass(frozen=True)
class Evidence:
    engine_type: str
    name: str
    measured_kind: str | None
    key_algorithm: str | None
    key_formats: tuple[str, ...]
    key_classes: tuple[str, ...]


@dataclass(frozen=True)
class Context:
    families: Families
    names: Names
    generator_kind: Callable[[str], str | None]
    listed_kind: Callable[[str, str], str | None]


Rule = Callable[[Evidence, Context], str | None]


def _known(ctx: Context, engine_type: str) -> list[str]:
    return ctx.families.key_kinds(engine_type)


def catalogue(e: Evidence, ctx: Context) -> str | None:
    """The family that lists the name decides, where the engine type does not: a listed name needs no evidence."""
    listed = ctx.listed_kind(e.engine_type, e.name)
    return listed if listed == UNKNOWN or len(_known(ctx, e.engine_type)) > 1 else None


def measured(e: Evidence, ctx: Context) -> str | None:
    return e.measured_kind if e.measured_kind in _known(ctx, e.engine_type) else None


def engine_type(e: Evidence, ctx: Context) -> str | None:
    kinds = _known(ctx, e.engine_type)
    return kinds[0] if len(kinds) == 1 else None


def key_generator(e: Evidence, ctx: Context) -> str | None:
    return ctx.generator_kind(e.key_algorithm) if e.key_algorithm else None


def declared(e: Evidence, ctx: Context) -> str | None:
    formats = {ctx.names.key_format(f).name for f in e.key_formats}
    if "RAW" in formats:
        return SECRET
    if formats & {"PKCS#8", "X.509"}:
        return PAIR
    classes = " ".join(e.key_classes)
    if "SecretKey" in classes:
        return SECRET
    if "PrivateKey" in classes or "PublicKey" in classes:
        return PAIR
    return None


RULES: tuple[tuple[str, Rule], ...] = ((FROM_CATALOGUE, catalogue), ("measured", measured), ("engine_type", engine_type),
                                       ("key_generator", key_generator), ("declared", declared))


def key_kind(e: Evidence, ctx: Context) -> tuple[str, str]:
    """UNKNOWN: no family fits, so the item is unidentified."""
    for name, rule in RULES:
        kind = rule(e, ctx)
        if kind == UNKNOWN:
            return UNKNOWN, name
        if kind is not None and kind in ctx.families.key_kinds(e.engine_type):
            return kind, name
    return UNKNOWN, "none"
