"""log/details/primitives_missing.yaml (schema 1): the primitives and providers an app uses that this run skipped or
stopped on because they are not available; its reasons, actions and the pointer line."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace

from .dossier import NOT_ON_DEVICE, VARIANT_NOT_MEASURED

SCHEMA_VERSION = 1
SKIPPED, STOPPED = "skipped", "stopped"
ACTIONS = (SKIPPED, STOPPED)
ABSENT_ON_DEVICE, BUNDLED_MISSING, HOST_CANNOT_BUILD = "absent_on_device", "bundled_missing", "host_cannot_build"
NOT_SCREENED, NOT_MEASURED, NO_DEVICE_ITEM = "not_screened", "not_measured", "no_device_item"
REASONS = (NOT_ON_DEVICE, ABSENT_ON_DEVICE, BUNDLED_MISSING, HOST_CANNOT_BUILD, NOT_SCREENED, NOT_MEASURED, NO_DEVICE_ITEM,
           VARIANT_NOT_MEASURED)
POINTER = "## to check primitives skipped or stopped due to not downloading them go {path}"


def pointer_line(path) -> str:
    return POINTER.format(path=path)


@dataclass(frozen=True)
class MissingRow:
    """primitive: `<engine type> <algorithm>`, None on a provider's row; provider: None when the site names none."""
    primitive: str | None
    provider: str | None
    reason: str
    apps: tuple[str, ...]
    sites: int
    action: str
    coordinates: tuple[str, ...]
    next: str

    @property
    def key(self) -> tuple:
        return self.primitive or "", self.provider or "", self.reason

    def merged(self, other: MissingRow) -> MissingRow:
        return replace(self, apps=tuple(sorted({*self.apps, *other.apps})), sites=self.sites + other.sites,
                       action=STOPPED if STOPPED in (self.action, other.action) else SKIPPED,
                       coordinates=tuple(sorted({*self.coordinates, *other.coordinates})))

    def to_json(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items()}


def missing_document(run: str, rows: list[MissingRow]) -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "run": run, "missing": [r.to_json() for r in rows]}
