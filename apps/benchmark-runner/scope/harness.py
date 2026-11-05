"""Reads perf-repair's harness.yaml into one HarnessScope per scope, with both function sources loaded."""
import pathlib, re
from dataclasses import dataclass

import yaml

from scope import languages as scope_languages

SCOPE_KEYS = {"id", "language", "function", "before", "after", "imports", "inputs", "current", "option", "metrics", "dependencies", "notMeasurable", "inverse", "callSite", "upgrade"}
ID = re.compile(r"^[0-9a-f]{12}$")
SCHEMA_VERSION = 6
INPUT_SOURCES = ("app", "run")


class HarnessError(Exception):
    pass


@dataclass(frozen=True)
class HarnessScope:
    id: str
    language: str
    function: str
    before: str
    after: str
    imports: tuple
    input_size: int | None
    key_size: int | None
    input_source: str
    current: str | None
    option: str | None
    metrics: tuple
    dependencies: tuple
    not_measurable: str | None = None
    inverse: dict | None = None
    call_site: dict | None = None
    upgrade: bool = False


@dataclass(frozen=True)
class Harness:
    app: str
    scopes: tuple


def read(path):
    path = pathlib.Path(path)
    if not path.is_file():
        raise HarnessError(f"missing_file: {path} (--harness)")
    document = yaml.safe_load(path.read_text()) or {}
    if document.get("schemaVersion") != SCHEMA_VERSION:
        raise HarnessError(f"unsupported_schema: {path} schemaVersion {document.get('schemaVersion')}, expected {SCHEMA_VERSION}")
    if not document.get("app"):
        raise HarnessError(f"missing_field: {path} app")
    scopes = tuple(scope(entry, index, path.parent) for index, entry in enumerate(document.get("scopes") or []))
    if not scopes:
        raise HarnessError(f"missing_field: {path} scopes")
    ids = [s.id for s in scopes]
    if len(ids) != len(set(ids)):
        raise HarnessError(f"duplicate_id: {path} scope ids repeat")
    return Harness(str(document["app"]), scopes)


def scope(entry, index, base):
    where = f"scopes[{index}]"
    if not isinstance(entry, dict):
        raise HarnessError(f"not_a_mapping: {where}")
    unknown = set(entry) - SCOPE_KEYS
    missing = {"id", "language", "function", "before", "after"} - set(entry)
    if unknown or missing:
        raise HarnessError(f"invalid_keys: {where} unknown {sorted(unknown)}, missing {sorted(missing)}")
    if not ID.match(str(entry["id"])):
        raise HarnessError(f"invalid: {where}.id {entry['id']}, expected 12 hex")
    if entry["language"] not in scope_languages.LANGUAGES:
        raise HarnessError(f"invalid: {where}.language {entry['language']}, known {list(scope_languages.LANGUAGES)}")
    inputs = entry.get("inputs") or {}
    if inputs.get("from") not in INPUT_SOURCES:
        raise HarnessError(f"invalid: {where}.inputs.from {inputs.get('from')}, known {list(INPUT_SOURCES)}")
    return HarnessScope(
        id=str(entry["id"]), language=entry["language"], function=str(entry["function"]),
        before=source(base, entry["before"], f"{where}.before"), after=source(base, entry["after"], f"{where}.after"),
        imports=tuple(str(line) for line in entry.get("imports") or ()),
        input_size=size(inputs.get("inputSize"), f"{where}.inputs.inputSize"),
        key_size=size(inputs.get("keySize"), f"{where}.inputs.keySize"), input_source=inputs["from"],
        current=entry.get("current"), option=entry.get("option"), metrics=tuple(entry.get("metrics") or ()),
        dependencies=tuple(str(name) for name in entry.get("dependencies") or ()),
        not_measurable=entry.get("notMeasurable"), inverse=entry.get("inverse"), call_site=call_site(entry.get("callSite"), where),
        upgrade=entry.get("upgrade") is True,
    )


def call_site(value, where):
    if value is not None and (not isinstance(value, dict) or set(value) != {"operation", "variant"}):
        raise HarnessError(f"invalid: {where}.callSite {value}, expected {{operation, variant}}")
    return value


def source(base, value, where):
    path = pathlib.Path(value)
    path = path if path.is_absolute() else base / path
    if not path.is_file():
        raise HarnessError(f"missing_file: {path} ({where})")
    return path.read_text()


def size(value, where):
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise HarnessError(f"not_positive: {where} {value}")
    return value
