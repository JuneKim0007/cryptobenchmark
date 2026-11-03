"""A scope's current item against one candidate of its family: the pair diff, the floor, availability, the change class."""
from __future__ import annotations

from dataclasses import dataclass

from ..catalog.types import Types
from ..dto.change import LOCAL_EDIT, MIGRATION, REJECTED, SAME, Change, PairDiff
from ..dto.site import Scope
from ..dto.types import NO_NONCE, NO_PARAMETERS, TypeRow

LOCAL_SINKS, RETURN_SINKS = {"local"}, {"local", "return"}
# a value built in the function itself can be rebuilt there for another parameter shape
RESHAPEABLE = ("generated", "literal", "derived")
FRESH = "generated"


@dataclass(frozen=True)
class Candidate:
    """bundled: its provider ships in the app, so the platform's minSdk does not bound it; lowers: screening refuses it."""
    item: str
    row: TypeRow | None
    measured: bool
    bundled: bool
    lowers: bool


def reach(scope: Scope) -> str:
    sinks = set(scope.sinks)
    return "local" if sinks <= LOCAL_SINKS else "return" if sinks <= RETURN_SINKS else "persist"


def _origin(scope: Scope, name: str) -> str:
    r = scope.lifecycle.origin_of(name) if scope.lifecycle is not None else None
    if r is None:
        return "unknown"
    return r.settled.origin if r.settled is not None else r.origin


def _input(scope: Scope, current: TypeRow, candidate: TypeRow) -> str:
    mine, theirs = current.properties.parameters, candidate.properties.parameters
    if mine == theirs:
        return SAME
    if mine == NO_PARAMETERS:
        return "new_parameter"
    return "reshaped" if theirs == NO_PARAMETERS or _origin(scope, "parameters") in RESHAPEABLE else "new_parameter"


def _key(current: TypeRow, candidate: TypeRow) -> str:
    if current.properties.keyType != candidate.properties.keyType:
        return "type"
    return "size" if current.strength.key != candidate.strength.key else SAME


def diff(scope: Scope, current: TypeRow, candidate: TypeRow) -> PairDiff:
    output = "kind" if current.outputKind != candidate.outputKind else "bytes"
    return PairDiff(_input(scope, current, candidate), _key(current, candidate), output, reach(scope))


def _floor(types: Types, scope: Scope, current: TypeRow, candidate: TypeRow) -> list[str]:
    if current.strength == candidate.strength:
        return []
    mine, theirs = types.strength(current, scope.keySize), types.strength(candidate, scope.keySize)
    if mine is None or theirs is None:
        return ["strength_unknown"]
    return ["strength_below"] if theirs < mine else []


def _nonce(scope: Scope, current: TypeRow, candidate: TypeRow) -> list[str]:
    mine, theirs = current.properties.nonceRequired, candidate.properties.nonceRequired
    stricter = theirs != mine and NO_NONCE not in (mine, theirs)
    return ["nonce_not_generated"] if stricter and _origin(scope, "parameters") != FRESH else []


def _lost(types: Types, current: TypeRow, candidate: TypeRow) -> list[str]:
    mine, theirs = current.properties, candidate.properties
    lost = ["authenticated_lost"] if mine.authenticated and not theirs.authenticated else []
    relied = current.outputKind in types.deterministic_relied
    return lost + (["deterministic_lost"] if relied and mine.deterministic and not theirs.deterministic else [])


def _available(c: Candidate, min_sdk: int | None) -> list[str]:
    if c.bundled:
        return []
    if c.row.minSdk is None or min_sdk is None:
        return ["availability_unknown"]
    return ["unavailable"] if min_sdk < c.row.minSdk else []


def rejects(types: Types, scope: Scope, current: TypeRow | None, c: Candidate, min_sdk: int | None) -> list[str]:
    if current is None or c.row is None:
        return ["type_unknown"]
    found = _floor(types, scope, current, c.row) + _lost(types, current, c.row) + _nonce(scope, current, c.row)
    found += _available(c, min_sdk) + ["not_measured"] * (not c.measured) + ["deprecated"] * c.lowers
    return found


def _class(scope: Scope, d: PairDiff) -> str:
    rekeyed = d.key == "type" or (d.key == "size" and scope.keySource != FRESH)
    if d.reach == "persist" or rekeyed or d.input == "new_parameter" or d.output == "kind":
        return MIGRATION
    return LOCAL_EDIT


def classify(types: Types, scope: Scope, current: TypeRow | None, c: Candidate, min_sdk: int | None) -> Change:
    """A candidate outside the current item's group: rejected with every reason found, else its class from the diff."""
    found = rejects(types, scope, current, c, min_sdk)
    if found:
        d = diff(scope, current, c.row) if current is not None and c.row is not None else PairDiff.same(reach(scope))
        return Change(c.item, REJECTED, d, tuple(found))
    d = diff(scope, current, c.row)
    return Change(c.item, _class(scope, d), d)
