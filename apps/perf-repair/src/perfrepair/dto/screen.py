from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from . import classify as answer
from cryptobench.document import DocumentKind

SCHEMA_VERSION = 5
SCREEN_DOC = DocumentKind("screen", SCHEMA_VERSION)
BROKEN, PLATFORM_DEPRECATED, ACCEPTED, UNKNOWN = "broken", "platform_deprecated", "accepted", "unknown"
UNVERIFIED = "unverified"
STATUSES = (BROKEN, PLATFORM_DEPRECATED, UNVERIFIED, ACCEPTED, UNKNOWN)
# unverified and unknown tie: a model's accepted is not evidence, so a swap between them lowers nothing.
RANK = {BROKEN: 0, PLATFORM_DEPRECATED: 1, UNVERIFIED: 2, UNKNOWN: 2, ACCEPTED: 3}
CODE_GROUPED = (BROKEN, PLATFORM_DEPRECATED)
MODEL_SOURCE = "model:"
MODEL_STATUS = {answer.DEPRECATED: BROKEN, answer.ACCEPTED: UNVERIFIED}


@dataclass(frozen=True)
class Verdict:
    status: str
    reason: str
    source: str | None = None
    canonical: str | None = None
    keySize: int | None = None
    providerHeld: bool = False

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Verdict":
        return cls(d["status"], d["reason"], d.get("source"), d.get("canonical"), d.get("keySize"),
                   bool(d.get("providerHeld")))


def with_answer(verdict: Verdict, answer: str, reason: str, fingerprint: str) -> Verdict:
    """A model answer on an unknown verdict: deprecated is broken at once, accepted only unverified, unsure unchanged."""
    status = MODEL_STATUS.get(answer)
    return verdict if status is None else replace(verdict, status=status, reason=reason,
                                                   source=MODEL_SOURCE + fingerprint)


def refused_target(current: Verdict | None, target: Verdict | None) -> bool:
    """A broken target is refused always; another status short of accepted only as the current item's own algorithm."""
    if target is None or target.status == ACCEPTED:
        return False
    if target.status == BROKEN:
        return True
    same = current is not None and target.canonical is not None and target.canonical == current.canonical
    return not same or RANK[target.status] < RANK[current.status]


def qualified_verdicts(groups: dict, screen: dict[int, Verdict] | None) -> dict[str, Verdict] | None:
    """screen.json's verdicts keyed by groups.json's qualified names; None without screen.json."""
    if screen is None:
        return None
    return {e["qualified"]: screen[int(k)] for k, e in groups["items"].items()}


def screen_document(verdicts: dict[int, Verdict], catalog: dict, built: dict, review: str | None = None) -> dict:
    """catalog: {source, sha256} of the screening catalog; built: {items, profiles} sha256 of the files these verdicts
    screen; review: the classify outbox fingerprint, only when it ran."""
    doc = {"schemaVersion": SCHEMA_VERSION, "catalog": catalog, "built": built}
    if review is not None:
        doc["review"] = {"fingerprint": review}
    return {**doc, "verdicts": {str(k): v.to_json() for k, v in sorted(verdicts.items())}}


def _checked(doc: dict) -> dict:
    SCREEN_DOC.check(doc)
    return doc


def read_screen(doc: dict) -> dict[int, Verdict]:
    return {int(k): Verdict.from_json(v) for k, v in _checked(doc)["verdicts"].items()}


def read_screen_catalog(doc: dict) -> dict:
    return _checked(doc)["catalog"]


def read_screen_built(doc: dict) -> dict:
    return _checked(doc)["built"]


def read_screen_review(doc: dict) -> str | None:
    return (_checked(doc).get("review") or {}).get("fingerprint")

