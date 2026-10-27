"""Reads perf-repair's harness.yaml into one HarnessScope per scope, with both function sources loaded."""
import pathlib, re
from dataclasses import dataclass

import yaml

LANGUAGES = ("java", "kotlin")
SCOPE_KEYS = {"id", "language", "function", "before", "after", "imports", "inputs", "option", "metrics", "dependencies"}
ID = re.compile(r"^[0-9a-f]{12}$")


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
    option: str | None
    metrics: tuple
    dependencies: tuple


@dataclass(frozen=True)
class Harness:
    app: str
    scopes: tuple


def read(path):
    path = pathlib.Path(path)
    if not path.is_file():
        raise HarnessError(f"missing_file: {path} (--harness)")
    document = yaml.safe_load(path.read_text()) or {}
    if document.get("schemaVersion") != 1:
        raise HarnessError(f"unsupported_schema: {path} schemaVersion {document.get('schemaVersion')}, expected 1")
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
    if entry["language"] not in LANGUAGES:
        raise HarnessError(f"invalid: {where}.language {entry['language']}, known {list(LANGUAGES)}")
    inputs = entry.get("inputs") or {}
    return HarnessScope(
        id=str(entry["id"]), language=entry["language"], function=str(entry["function"]),
        before=source(base, entry["before"], f"{where}.before"), after=source(base, entry["after"], f"{where}.after"),
        imports=tuple(str(line) for line in entry.get("imports") or ()),
        input_size=size(inputs.get("inputSize"), f"{where}.inputs.inputSize"),
        key_size=size(inputs.get("keySize"), f"{where}.inputs.keySize"),
        option=entry.get("option"), metrics=tuple(entry.get("metrics") or ()),
        dependencies=tuple(str(name) for name in entry.get("dependencies") or ()),
    )


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
