"""A lifecycle's status and reasons from what the slice found; `bounded` only when one method holds it end to end."""
from __future__ import annotations

from dataclasses import dataclass

from ...dto.lifecycle import BOUNDED, NO_REAL_USE, PARTIALLY_BOUNDED

_ONE_METHOD = ("local", "chain")


@dataclass(frozen=True)
class Found:
    """configured, used: `same`, `depth1` or None (not found); configured is `same` when the engine needs none."""
    binding: str
    configured: str | None
    used: str | None
    escapes: bool
    wrapper: bool
    deferred: bool
    over_budget: bool
    private_field: bool


def _no_real_use(f: Found) -> bool:
    held = f.binding in ("local", "chain", "discarded") or f.binding == "field" and f.private_field
    return f.used is None and not f.wrapper and not f.escapes and held


def status(f: Found) -> tuple[str, tuple[str, ...]]:
    if _no_real_use(f):
        return NO_REAL_USE, ()
    reasons = [r for r, on in (
        ("field", f.binding == "field"),
        ("escape", f.escapes or f.binding not in _ONE_METHOD + ("field",)),
        ("wrapper", f.wrapper),
        ("deferred", f.deferred),
        ("depth1", "depth1" in (f.configured, f.used)),
        ("budget", f.over_budget),
        ("configuration_not_found", f.configured is None),
        ("use_not_found", f.used is None and not f.wrapper),
    ) if on]
    return (PARTIALLY_BOUNDED, tuple(reasons)) if reasons else (BOUNDED, ())
