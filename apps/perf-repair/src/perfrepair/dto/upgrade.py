"""upgrades.json: what each broken use became; dossiers.json's upgrades rows, one broken use's slice for the upgrade role."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from cryptobench.document import DocumentKind
from .dossier import Dossier
from .replacement import Edit, Replacement

SCHEMA_VERSION = 1
UPGRADES_DOC = DocumentKind("upgrades", SCHEMA_VERSION)
UPGRADED, NEEDS_MIGRATION, NO_SECURE, NOT_REACHED = "upgraded", "needs_migration", "no_secure_option", "not_reached"
STATUSES = (UPGRADED, NEEDS_MIGRATION, NO_SECURE, NOT_REACHED)
# who settled a row: the upgrade list, the model, the dropped-answer fallback, or code when nothing could be offered
LIST_SOURCE, MODEL_SOURCE, FALLBACK_SOURCE, STATIC_SOURCE = "list", "llm", "fallback", "static"
SOURCES = (LIST_SOURCE, MODEL_SOURCE, FALLBACK_SOURCE, STATIC_SOURCE)


@dataclass(frozen=True)
class UpgradeItem:
    """A broken use with options, ranked; identified: the list names them; linked: its unit's other members."""
    dossier: Dossier
    identified: bool
    linked: tuple[str, ...] = ()
    providerHeld: bool = False
    # per option item, per selected metric, its own median at this site: a key size the current lacks leaves no ratio
    measured: dict[str, dict[str, float | None]] = field(default_factory=dict)
    # why screening refuses the current item
    screenReason: str = ""

    @property
    def key(self) -> str:
        return self.dossier.key

    def to_json(self) -> dict:
        return {**self.dossier.to_json(), "identified": self.identified, "linked": list(self.linked),
                "providerHeld": self.providerHeld, "measured": self.measured, "screenReason": self.screenReason}

    @classmethod
    def from_json(cls, d: dict) -> "UpgradeItem":
        return cls(Dossier.from_json(d), d["identified"], tuple(d["linked"]), d["providerHeld"], d["measured"], d["screenReason"])


@dataclass(frozen=True)
class Upgrade:
    """option: the chosen item, None when none was chosen; edits: only an upgraded row's; needs: what a person must settle;
    review: code's facts a person checks, the option's needsReview."""
    scope: str
    current: str
    status: str
    option: str | None
    source: str
    reason: str
    edits: tuple[Edit, ...] = ()
    needs: tuple[str, ...] = ()
    review: tuple[str, ...] = ()

    def replacement(self) -> Replacement:
        """An upgraded row as the replace decision the edit step applies."""
        return Replacement(self.scope, "replace", self.option, self.edits, (), self.reason)

    def to_json(self) -> dict:
        return {"scope": self.scope, "current": self.current, "status": self.status, "option": self.option,
                "source": self.source, "reason": self.reason, "edits": [asdict(e) for e in self.edits],
                "needs": list(self.needs), "review": list(self.review)}

    @classmethod
    def from_json(cls, d: dict) -> "Upgrade":
        return cls(d["scope"], d["current"], d["status"], d["option"], d["source"], d["reason"],
                   tuple(Edit(**e) for e in d["edits"]), tuple(d["needs"]), tuple(d["review"]))


def read_upgrades(doc: dict) -> list[Upgrade]:
    UPGRADES_DOC.check(doc)
    return [Upgrade.from_json(u) for u in doc["upgrades"]]
