"""Lifecycle and Requirement: a primitive object followed from its creation to its last use, as evidence on a Scope."""
from __future__ import annotations

from dataclasses import dataclass

BOUNDED, PARTIALLY_BOUNDED, NO_REAL_USE, UNSUPPORTED = "bounded", "partially_bounded", "no_real_use", "unsupported"
STATUSES = (BOUNDED, PARTIALLY_BOUNDED, NO_REAL_USE, UNSUPPORTED)
BINDINGS = ("chain", "local", "field", "returned", "argument", "discarded", "other")
# unsupported: why nothing was read; partially_bounded: why the reading is not one method end to end
UNSUPPORTED_REASONS = ("parser_missing", "engine_unknown", "call_not_found")
PARTIAL_REASONS = ("field", "escape", "wrapper", "deferred", "depth1", "budget", "configuration_not_found",
                   "use_not_found")
REASONS = UNSUPPORTED_REASONS + PARTIAL_REASONS
ROLES = ("configure", "use", "consume", "other")
WHERE = ("same", "depth1")
REQUIREMENTS = ("key", "parameters", "input")
ORIGINS = ("parameter", "field", "same_class_call", "other_call", "generated", "derived", "keystore", "decoded",
           "storage", "literal", "unknown")
# code cannot say from the value alone where it finally comes from
OPEN_ORIGINS = ("parameter", "field", "same_class_call", "other_call", "unknown")


@dataclass(frozen=True)
class Step:
    """One call on the object: its role from engines.yaml, the call's name and line, in the site's method or one away."""
    role: str
    call: str
    line: int
    where: str


@dataclass(frozen=True)
class Settled:
    """The one closed origin every path of an open requirement reaches, and its line in the scope's file."""
    origin: str
    line: int


@dataclass(frozen=True)
class Requirement:
    """A value a step needs: origin is where code reads it from at `line` and is never rewritten; at is the step's line;
    depth1 the origins one method away when origin is a field or a parameter of a private method; settled what code closed it to."""
    name: str
    origin: str
    line: int
    at: int
    depth1: tuple[str, ...] = ()
    settled: Settled | None = None

    @property
    def open(self) -> bool:
        """A closed depth1 settles it, as the key source view reads it."""
        return self.origin in OPEN_ORIGINS and not (len(self.depth1) == 1 and self.depth1[0] not in OPEN_ORIGINS)

    def to_json(self) -> dict:
        return {**vars(self), "depth1": list(self.depth1), "settled": vars(self.settled) if self.settled else None}

    @classmethod
    def from_json(cls, d: dict) -> "Requirement":
        settled = d.get("settled")
        return cls(**{**d, "depth1": tuple(d["depth1"]), "settled": Settled(**settled) if settled else None})


@dataclass(frozen=True)
class Lifecycle:
    """operations: the benchmark operations the steps perform; empty when unknown."""
    status: str
    reasons: tuple[str, ...] = ()
    binding: str | None = None
    steps: tuple[Step, ...] = ()
    requirements: tuple[Requirement, ...] = ()
    operations: tuple[str, ...] = ()

    @classmethod
    def unsupported(cls, reason: str) -> "Lifecycle":
        return cls(UNSUPPORTED, (reason,))

    def to_json(self) -> dict:
        return {"status": self.status, "reasons": list(self.reasons), "binding": self.binding,
                "steps": [vars(s) for s in self.steps],
                "requirements": [r.to_json() for r in self.requirements],
                "operations": list(self.operations)}

    @classmethod
    def from_json(cls, d: dict) -> "Lifecycle":
        return cls(d["status"], tuple(d["reasons"]), d["binding"], tuple(Step(**s) for s in d["steps"]),
                   tuple(Requirement.from_json(r) for r in d["requirements"]), tuple(d["operations"]))

    def origin_of(self, name: str) -> Requirement | None:
        return next((r for r in self.requirements if r.name == name), None)
