"""Crypto libraries the app declares in Gradle and the version catalog, and the providers its code registers."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ...files import read_yaml
from ...source.code import Code
from ...source.language import of_build_file
from ...source.lexer import mask
from ..find.imports import import_reason
from .versions import pinned_versions

LIBRARIES = Path(__file__).with_name("libraries.yaml")
REGISTRY = "Security"
SUPPORTED_SCHEMA = 1

_COORDINATE = re.compile(r"""["']([\w.\-]+):([\w.\-]+)(?::[^"'\s]*)?["']""")
_MAP = re.compile(r"""group\s*[:=]\s*["']([\w.\-]+)["']\s*,\s*name\s*[:=]\s*["']([\w.\-]+)["']""")
_REGISTER = re.compile(rf"\b{REGISTRY}\s*\.\s*(addProvider|insertProviderAt)\s*\(")


@dataclass(frozen=True)
class Library:
    group: str
    name: str
    providerName: str | None


@dataclass(frozen=True)
class Bundled:
    artifact: str
    providerName: str | None
    version: str | None = None


@dataclass(frozen=True)
class Registration:
    file: str
    line: int
    expr: str
    call: str | None = None
    # the position argument's text; None for a call that takes none
    position: str | None = None

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


def coordinates(texts: list[tuple[Path, str]]) -> set[tuple[str, str]]:
    found = set()
    for _, text in texts:
        found |= {(m.group(1), m.group(2)) for m in _COORDINATE.finditer(text)}
        found |= {(m.group(1), m.group(2)) for m in _MAP.finditer(text)}
    return found


def bundled(build_files: list[Path], libraries: list[Library]) -> list[Bundled]:
    """Each crypto library declared, with its pinned version when the build files hold one."""
    texts = [(path, _uncommented(path)) for path in build_files]
    versions, out = pinned_versions(texts), {}
    for group, name in coordinates(texts):
        hit = next((lib for lib in libraries if lib.group == group and name.startswith(lib.name)), None)
        if hit is not None:
            artifact = f"{group}:{name}"
            out[artifact] = Bundled(artifact, hit.providerName, versions.get(artifact))
    return [out[k] for k in sorted(out)]


def registrations(code: Code, rel: str) -> list[Registration]:
    out = []
    for m in _REGISTER.finditer(code.masked):
        if import_reason(code, REGISTRY, m.start()) is not None:
            continue
        parsed = code.arguments(m.end() - 1)
        if parsed and parsed[0]:
            args = [" ".join(a.split()) for a in parsed[0]]
            out.append(Registration(rel, code.line(m.start()), args[0], m.group(1), args[1] if len(args) > 1 else None))
    return out
