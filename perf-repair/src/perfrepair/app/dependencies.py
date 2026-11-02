"""Crypto libraries the app declares in Gradle and the version catalog, and the providers its code registers."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..files import read_yaml
from ..source.language import of_build_file
from ..source.lexer import Code, mask
from .imports import import_reason

LIBRARIES = Path(__file__).with_name("libraries.yaml")
REGISTRY = "Security"
SUPPORTED_SCHEMA = 1

_COORDINATE = re.compile(r"""["']([\w.\-]+):([\w.\-]+)(?::[^"'\s]*)?["']""")
_MAP = re.compile(r"""group\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*name\s*[:=]\s*["']([\w.\-]+)["']""")
_REGISTER = re.compile(rf"\b{REGISTRY}\s*\.\s*(?:addProvider|insertProviderAt)\s*\(")


@dataclass(frozen=True)
class Library:
    group: str
    name: str
    providerName: str | None


@dataclass(frozen=True)
class Bundled:
    artifact: str
    providerName: str | None


@dataclass(frozen=True)
class Registration:
    file: str
    line: int
    expr: str

    def to_json(self) -> dict:
        return asdict(self)


def read_libraries(path: Path = LIBRARIES) -> list[Library]:
    doc = read_yaml(path)
    if doc.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"{path}: schemaVersion {doc.get('schemaVersion')} is not {SUPPORTED_SCHEMA}")
    return [Library(e["group"], e["name"] or "", e["providerName"]) for e in doc["libraries"]]


def _uncommented(path: Path) -> str:
    text = path.read_text(errors="replace")
    if path.suffix == ".toml":
        return "\n".join("" if line.lstrip().startswith("#") else line for line in text.splitlines())
    return mask(text, of_build_file(path.name), strings=False)


def coordinates(build_files: list[Path]) -> set[tuple[str, str]]:
    found = set()
    for path in build_files:
        text = _uncommented(path)
        found |= {(m.group(1), m.group(2)) for m in _COORDINATE.finditer(text)}
        found |= {(m.group(1), m.group(2)) for m in _MAP.finditer(text)}
    return found


def bundled(build_files: list[Path], libraries: list[Library]) -> list[Bundled]:
    out = {}
    for group, name in coordinates(build_files):
        hit = next((lib for lib in libraries if lib.group == group and name.startswith(lib.name)), None)
        if hit is not None:
            out[f"{group}:{name}"] = Bundled(f"{group}:{name}", hit.providerName)
    return [out[k] for k in sorted(out)]


def registrations(code: Code, rel: str) -> list[Registration]:
    out = []
    for m in _REGISTER.finditer(code.masked):
        if import_reason(code, REGISTRY, m.start()) is not None:
            continue
        parsed = code.arguments(m.end() - 1)
        if parsed and parsed[0]:
            out.append(Registration(rel, code.line(m.start()), " ".join(parsed[0][0].split())))
    return out
