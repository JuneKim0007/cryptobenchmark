"""replacements.json: Replacement, Edit and the edit-kind table; decisions, risks and the risks scope and option imply."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields

from .document import DocumentKind
from .dossier import Option
from .site import REPLACEMENTS_SCHEMA_VERSION, Scope

REPLACEMENTS_DOC = DocumentKind("replacements", REPLACEMENTS_SCHEMA_VERSION)

DECISIONS = ("replace", "keep", "recommend")
RECOMMEND = "recommend"
# what an answer's concerns may hold; their content is never gated
MAX_CONCERNS, MAX_CONCERN_LENGTH = 5, 300

RISKS = ("persisted_data", "wire_format", "key_compatibility", "unknown_sink", "unverified_interop")
# a replace that changes the output is refused when its own risks name one of these: callers or stored data must follow
OUTPUT_LEAVES = ("persisted_data", "wire_format", "unknown_sink")
# (scope or option field, value, risk it implies, plain words): the minimum risks a replace must declare
DERIVED_RISKS = (
    ("sinks", "persist", "persisted_data", "the output is stored and read back later"),
    ("sinks", "network", "wire_format", "the output leaves the process"),
    ("sinks", "unknown", "unknown_sink", "where the output goes is unknown"),
    ("keySource", "keystore", "key_compatibility", "the key lives in a key store"),
    ("keySource", "literal", "key_compatibility", "the key is a literal in the code"),
    ("keySource", "storage", "key_compatibility", "the key is read back from storage"),
    ("keySource", "unknown", "key_compatibility", "where the key comes from is not visible here"),
    ("keySource", "parameter", "key_compatibility", "where the key comes from is not visible here"),
    ("interop", "not_checkable", "unverified_interop", "the interop check could not decide the pair"),
    ("interop", "not_planned", "unverified_interop", "the pair was not in the interop plan"),
    ("interop", "not_run", "unverified_interop", "no interop check has run"),
)


def required_risks(scope: Scope, option: "Option | None" = None) -> dict[str, list[str]]:
    """Each risk the scope facts, and the chosen option's when given, imply, with the plain words that imply it."""
    out: dict[str, list[str]] = {}
    option_fields = {f.name for f in fields(Option)}
    for field_name, value, risk, words in DERIVED_RISKS:
        subject = option if field_name in option_fields else scope
        facts = getattr(subject, field_name) if subject is not None else ()
        if value in (facts if isinstance(facts, tuple) else (facts,)):
            out.setdefault(risk, []).append(words)
    return out


@dataclass(frozen=True)
class EditKind:
    """`field` of an Edit is the one this kind fills, with the chosen option's `takes`; the other fields stay empty."""
    field: str
    takes: str
    phrase: str
    meaning: str
    value: str
    required: str


EDIT_FIELDS = ("provider", "algorithm", "parameters")
EDIT_KIND_TABLE = {
    "set_provider": EditKind("provider", "provider", "is provided by",
                             "construct the call's engine from the chosen option's provider", "that name exactly",
                             "when the option's provider differs from the current one"),
    "set_algorithm": EditKind("algorithm", "algorithm", "is named",
                              "request the chosen option's name instead of the current one", "that name exactly",
                              "when the option's name differs from the current one"),
    "pin_parameters": EditKind("parameters", "pins", "lists",
                               "state the option's pins at the call so the result stays like-for-like",
                               "every pin as {name, value}, exactly as listed",
                               "when the option lists pins; not allowed when it lists none"),
}
EDIT_KINDS = tuple(EDIT_KIND_TABLE)


@dataclass(frozen=True)
class Edit:
    kind: str
    provider: str | None = None
    algorithm: str | None = None
    parameters: dict | None = None


@dataclass(frozen=True)
class Replacement:
    """The model's decision for one scope, after its gate: which option, and the edits from EDIT_KINDS that apply it."""
    scope: str
    decision: str
    option: str | None
    edits: tuple[Edit, ...]
    risks: tuple[str, ...]
    reason: str
    # the metrics the model named as deciding and the losses it accepted; a recommend's needs; anything it found odd
    deciding: tuple[str, ...] = ()
    accepted: tuple[str, ...] = ()
    needs: tuple[str, ...] = ()
    concerns: tuple[str, ...] = ()

    def to_json(self) -> dict:
        return {"scope": self.scope, "decision": self.decision, "option": self.option,
                "edits": [asdict(e) for e in self.edits], "risks": list(self.risks), "reason": self.reason,
                "deciding": list(self.deciding), "accepted": list(self.accepted), "needs": list(self.needs),
                "concerns": list(self.concerns)}

    @classmethod
    def from_json(cls, d: dict) -> "Replacement":
        return cls(d["scope"], d["decision"], d.get("option"), tuple(Edit(**e) for e in d.get("edits") or ()),
                   tuple(d.get("risks") or ()), d["reason"], *(tuple(d.get(k) or ()) for k in ("deciding", "accepted", "needs", "concerns")))


def read_replacements(doc: dict) -> dict[str, Replacement]:
    REPLACEMENTS_DOC.check(doc)
    return {r["scope"]: Replacement.from_json(r) for r in doc["replacements"]}
