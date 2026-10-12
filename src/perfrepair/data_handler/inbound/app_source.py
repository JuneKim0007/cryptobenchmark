from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ...dto import ProviderEntry
from .probe_index import ProbeIndex

SOURCE_SUFFIXES = (".java", ".kt")
IGNORED_DIRS = {"build", ".gradle", ".git", ".idea", "node_modules"}

_STRING = re.compile(r'^"((?:[^"\\]|\\.)*)"$')
_GET_PROVIDER = re.compile(r'getProvider\s*\(\s*"((?:[^"\\]|\\.)*)"\s*\)')


@dataclass(frozen=True)
class Argument:
    expr: str
    literal: str | None


@dataclass(frozen=True)
class Site:
    file: str
    line: int
    engineType: str
    algorithm: Argument
    provider: Argument | None
    snippet: str

    def to_json(self) -> dict:
        return asdict(self)


def _split_args(text: str, start: int) -> tuple[list[str], int] | None:
    """Top-level arguments of the call whose '(' is at text[start - 1]."""
    depth, i, quote, args, cur = 0, start, None, [], []
    while i < len(text):
        ch = text[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(text):
                cur.append(text[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            if depth == 0:
                args.append("".join(cur).strip())
                return [a for a in args if a], i
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    return None


def _argument(expr: str, provider: bool = False) -> Argument:
    m = _STRING.match(expr)
    if m:
        return Argument(expr, m.group(1))
    if provider:
        m = _GET_PROVIDER.search(expr)
        if m:
            return Argument(expr, m.group(1))
    return Argument(expr, None)


def scan(root: Path, engine_types: set[str]) -> list[Site]:
    root = Path(root)
    if not engine_types:
        return []
    call = re.compile(r"\b(" + "|".join(sorted(map(re.escape, engine_types))) + r")\s*\.\s*getInstance\s*\(")
    sites: list[Site] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in SOURCE_SUFFIXES or IGNORED_DIRS & set(path.relative_to(root).parts):
            continue
        text = path.read_text(errors="replace")
        lines = text.splitlines()
        for m in call.finditer(text):
            parsed = _split_args(text, m.end())
            if not parsed or not parsed[0]:
                continue
            args, _ = parsed
            line = text.count("\n", 0, m.start()) + 1
            sites.append(Site(
                file=str(path.relative_to(root)),
                line=line,
                engineType=m.group(1),
                algorithm=_argument(args[0]),
                provider=_argument(args[1], provider=True) if len(args) > 1 else None,
                snippet=lines[line - 1].strip(),
            ))
    return sites


def default_provider(index: ProbeIndex, providers: list[ProviderEntry], engine_type: str,
                     algorithm: str) -> tuple[str, str] | None:
    for p in sorted(providers, key=lambda p: p.precedence):
        name = index.canonical(p.name, engine_type, algorithm)
        if name is not None:
            return p.name, name
    return None


def resolve(site: Site, index: ProbeIndex, providers: list[ProviderEntry]) -> dict:
    alg = site.algorithm.literal
    on_device = {p.name for p in providers}
    if site.provider is not None:
        name = site.provider.literal
        if name is None:
            provider, alg, resolution = None, None, "unresolved_provider"
        elif name not in on_device:
            provider, resolution = name, "provider_not_on_device"
        elif alg is None:
            provider, resolution = name, "unresolved_algorithm"
        else:
            provider, alg, resolution = name, index.canonical(name, site.engineType, alg) or alg, "explicit"
    elif alg is None:
        provider, resolution = None, "unresolved_algorithm"
    else:
        hit = default_provider(index, providers, site.engineType, alg)
        provider, alg, resolution = (hit[0], hit[1], "default") if hit else (None, alg, "not_registered")
    return site.to_json() | {"resolvedProvider": provider, "resolvedAlgorithm": alg, "resolution": resolution}
