"""The user's device aliases, ~/.config/cryptobench/devices.yaml: alias -> device key, one alias per key; no file is no aliases."""
from __future__ import annotations

from pathlib import Path

from cryptobench.shared.document.document import DocumentKind
from cryptobench.shared.errors.input_error import InputError

DEVICES_DOC = DocumentKind("devices", 1)
KEYS = ("schemaVersion", "aliases")


def read(path: Path) -> dict[str, str]:
    """An alias with a colon would read as an emulator or unstable key, so it is refused."""
    if not path.is_file():
        return {}
    doc = DEVICES_DOC.read(path)
    unknown = sorted(set(doc) - set(KEYS))
    if unknown:
        raise InputError(f"unknown_keys: {path}: {', '.join(unknown)}; known {', '.join(KEYS)}", path)
    aliases = doc.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise InputError(f"invalid_alias: {path}: aliases is a {type(aliases).__name__}, not a mapping", path)
    for alias, key in aliases.items():
        if not isinstance(alias, str) or not isinstance(key, str) or not alias.strip() or not key.strip() or ":" in alias:
            raise InputError(f"invalid_alias: {path}: {alias!r}: {key!r}; an alias and its key are non-blank text, the alias without ':'", path)
    keys = [key for key in aliases.values()]
    twice = sorted({key for key in keys if keys.count(key) > 1})
    if twice:
        raise InputError(f"duplicate_alias: {path}: {', '.join(twice)} named by more than one alias", path)
    return dict(aliases)
