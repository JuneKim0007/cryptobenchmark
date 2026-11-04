"""The bundled-providers catalog: per Gradle group:name, the providers.bundled entry that builds it into the harness;
every row checked, every problem reported at once."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..dto.coded import InputError
from ..dto.document import parse_yaml

BUNDLED_PROVIDERS = Path(__file__).with_name("bundled-providers.yaml")
SCHEMA_VERSION = 1
REQUIRED = ("artifact", "provider", "create", "source")
OPTIONAL = ("alias", "minSdk", "notes", "blocked", "badVersions")
# the forms config's BundledProvider accepts; the version is the app's pin, never the catalog's
_ARTIFACT = re.compile(r"^[\w.\-]+:[\w.\-]+$")
_CREATE = re.compile(r"^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)+(#[A-Za-z_$][\w$]*)?$")
_NAME = re.compile(r"^\S+$")
_FORMS = (("artifact", _ARTIFACT, "group:name"), ("create", _CREATE, "Class or Class#factory"),
          ("alias", _NAME, "a name without whitespace"), ("provider", _NAME, "a name without whitespace"))


class BundledCatalogError(InputError):
    pass


@dataclass(frozen=True)
class BundledRow:
    artifact: str
    provider: str
    create: str
    source: str
    alias: str | None = None
    minSdk: int | None = None
    notes: str | None = None
    blocked: str | None = None
    # versions that fail on a device: a pin here is never built
    badVersions: tuple[str, ...] = ()

    def registered_by(self, expr: str) -> bool:
        """An app's Security registration expression builds this row's provider: `Class.factory(` or `Class(`."""
        cls, _, factory = self.create.partition("#")
        made = f"{cls.rsplit('.', 1)[-1]}.{factory}(" if factory else f"{cls.rsplit('.', 1)[-1]}("
        return made in "".join(expr.split())

    def entry(self, version: str) -> dict:
        """The providers.bundled entry at the app's pinned version."""
        return {"artifact": f"{self.artifact}:{version}", "create": self.create,
                **({"alias": self.alias} if self.alias else {})}


@dataclass(frozen=True)
class BundledCatalog:
    rows: dict[str, BundledRow]

    @classmethod
    def load(cls, path: Path = BUNDLED_PROVIDERS) -> "BundledCatalog":
        doc = parse_yaml(Path(path).read_text(), str(path), "bundled_catalog_yaml", error=BundledCatalogError)
        problems = catalog_problems(doc)
        if problems:
            raise BundledCatalogError(f"bundled_catalog: {path}: " + "; ".join(problems))
        return cls({r["artifact"]: BundledRow(**r) for r in doc["providers"]})


def _form_problems(where: str, row: dict) -> list[str]:
    return [f"{where}: {k} {row[k]!r} is not {what}" for k, pattern, what in _FORMS
            if row.get(k) is not None and not (isinstance(row[k], str) and pattern.match(row[k]))]


def _value_problems(where: str, row: dict, sources: dict) -> list[str]:
    out = []
    if row.get("minSdk") is not None and not (type(row["minSdk"]) is int and row["minSdk"] > 0):
        out.append(f"{where}: minSdk {row['minSdk']!r} is not a positive integer")
    out += [f"{where}: {k} is blank" for k in ("notes", "blocked") if k in row and not (isinstance(row[k], str) and row[k].strip())]
    bad = row.get("badVersions")
    if bad is not None and not (isinstance(bad, list) and bad and all(isinstance(v, str) and v for v in bad)):
        out.append(f"{where}: badVersions {bad!r} is not a list of versions")
    if row.get("source") and row["source"] not in sources:
        out.append(f"{where}: source {row['source']!r} is not in sources")
    return out


def _row_problems(where: str, row, sources: dict) -> list[str]:
    if not isinstance(row, dict):
        return [f"{where}: not a mapping"]
    out = [f"{where}: no {k}" for k in REQUIRED if not row.get(k)]
    out += [f"{where}: unknown key {k}" for k in row if k not in REQUIRED + OPTIONAL]
    return out + _form_problems(where, row) + _value_problems(where, row, sources)


def _duplicates(rows: list) -> list[str]:
    # an alias may repeat (one provider, two artifacts): an app ships one of them, apply keeps the first
    artifacts = [r.get("artifact") for r in rows if isinstance(r, dict) and r.get("artifact")]
    return [f"duplicate artifact {a}" for a in sorted({a for a in artifacts if artifacts.count(a) > 1})]


def catalog_problems(doc) -> list[str]:
    if not isinstance(doc, dict) or doc.get("schemaVersion") != SCHEMA_VERSION:
        return [f"schemaVersion is not {SCHEMA_VERSION}"]
    sources, rows = doc.get("sources") or {}, doc.get("providers")
    if not isinstance(sources, dict) or not isinstance(rows, list):
        return ["sources must be a mapping and providers a list"]
    return [p for i, row in enumerate(rows) for p in _row_problems(f"providers[{i}]", row, sources)] + _duplicates(rows)
