"""Identifiers a function uses but does not define, from tokens alone: a best effort, never a compile check.

Members reached through another receiver (`a.b`) are not counted; `this.x` is. Wildcard imports hide nothing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..files import read_yaml
from ..source.language import Language
from ..source.lexer import mask

TABLE = Path(__file__).with_name("names.yaml")
# a number first, whole: `0xff` must not leave `xff` as a name; its fraction needs a digit, so `0..n` keeps `n`
_NUMBER = r"\d\w*(?:\.\d\w*)?(?:(?<=[eEpP])[-+]\d\w*)?"
_TOKEN = re.compile(rf"[A-Za-z_]\w*|{_NUMBER}|->|==|!=|<=|>=|\S")
_IDENT = re.compile(r"[A-Za-z_]\w*")
_IMPORT = re.compile(r"import\s+(?:static\s+)?([\w.]+)(?:\s+as\s+(\w+))?")
_DECLARED_BEFORE = {"=", ";", ",", ")", ":"}


@dataclass(frozen=True)
class Names:
    keywords: frozenset[str]
    types: frozenset[str]
    implicit: frozenset[str]
    conventions: frozenset[str] = frozenset()
    extensions: bool = False


def load(language: str, path: Path = TABLE) -> Names:
    table = read_yaml(path)
    d = table[language]
    return Names(frozenset(d["keywords"]), frozenset(d["types"]), frozenset(d["implicit"]) | frozenset(table["java_lang"]),
                 frozenset(d.get("conventions") or ()), bool(d.get("extensions")))


def tokens(masked: str) -> list[str]:
    return _TOKEN.findall(masked)


def imported(imports: list[str]) -> set[str]:
    """Simple names (or aliases) and root packages the import lines bring into scope."""
    names = set()
    for line in imports:
        m = _IMPORT.match(line.strip())
        if m:
            path = m.group(1).split(".")
            names |= {path[0], m.group(2) or path[-1]}
    return names - {"*"}


def imported_name(line: str) -> str | None:
    """The simple name or alias one import line brings in; none for a line that is no import."""
    m = _IMPORT.match(line.strip())
    return (m.group(2) or m.group(1).split(".")[-1]) if m else None


def _lambda_parameter(tokens: list[str], i: int) -> bool:
    j = i + 1
    while j < len(tokens) and (tokens[j] in {",", ")"} or _IDENT.fullmatch(tokens[j])):
        j += 1
    return j < len(tokens) and tokens[j] == "->"


def dependencies(function: str, language: Language, imports: list[str], names: Names) -> list[str]:
    found = tokens(mask(function, language))
    typed = lambda t: t == "]" or (bool(_IDENT.fullmatch(t)) and (t not in names.keywords or t in names.types))
    used, declared = set(), set()
    first_call = next((i - 1 for i, t in enumerate(found) if t == "(" and i), None)
    for i, t in enumerate(found):
        if not _IDENT.fullmatch(t) or t in names.keywords or t in names.types:
            continue
        prev = found[i - 1] if i else ""
        before = found[i - 2] if i > 1 else ""
        after = found[i + 1] if i + 1 < len(found) else ""
        if prev == "@" or (prev == "." and before not in {"this", "super"}):
            continue
        if (i == first_call or prev in {"val", "var", "fun"} or (typed(prev) and after in _DECLARED_BEFORE)
                or (prev in {"(", ","} and after == ":" and language.colon_types)
                or (prev == "(" and before == "for") or _lambda_parameter(found, i)):
            declared.add(t)
        else:
            used.add(t)
    return sorted(used - declared - names.implicit - imported(imports))
