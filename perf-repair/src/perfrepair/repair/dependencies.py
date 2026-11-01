"""Identifiers a function uses but does not define, from tokens alone: a best effort, never a compile check.

Members reached through another receiver (`a.b`) are not counted; `this.x` is. Wildcard imports hide nothing."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..app.lexer import mask
from ..dto.language import Language
from ..files import read_yaml

TABLE = Path(__file__).with_name("names.yaml")
_TOKEN = re.compile(r"[A-Za-z_]\w*|->|==|!=|<=|>=|\S")
_IDENT = re.compile(r"[A-Za-z_]\w*")
_IMPORT = re.compile(r"import\s+(?:static\s+)?([\w.]+)(?:\s+as\s+(\w+))?")
_DECLARED_BEFORE = {"=", ";", ",", ")", ":"}


@dataclass(frozen=True)
class Names:
    keywords: frozenset[str]
    types: frozenset[str]
    implicit: frozenset[str]


def load(language: str, path: Path = TABLE) -> Names:
    d = read_yaml(path)[language]
    return Names(frozenset(d["keywords"]), frozenset(d["types"]), frozenset(d["implicit"]))


def imported(imports: list[str]) -> set[str]:
    """Simple names (or aliases) and root packages the import lines bring into scope."""
    names = set()
    for line in imports:
        m = _IMPORT.match(line.strip())
        if m:
            path = m.group(1).split(".")
            names |= {path[0], m.group(2) or path[-1]}
    return names - {"*"}


def _lambda_parameter(tokens: list[str], i: int) -> bool:
    j = i + 1
    while j < len(tokens) and (tokens[j] in {",", ")"} or _IDENT.fullmatch(tokens[j])):
        j += 1
    return j < len(tokens) and tokens[j] == "->"


def dependencies(function: str, language: Language, imports: list[str], names: Names) -> list[str]:
    tokens = _TOKEN.findall(mask(function, language))
    typed = lambda t: t == "]" or (bool(_IDENT.fullmatch(t)) and (t not in names.keywords or t in names.types))
    used, declared = set(), set()
    first_call = next((i - 1 for i, t in enumerate(tokens) if t == "(" and i), None)
    for i, t in enumerate(tokens):
        if not _IDENT.fullmatch(t) or t in names.keywords or t in names.types:
            continue
        prev = tokens[i - 1] if i else ""
        before = tokens[i - 2] if i > 1 else ""
        after = tokens[i + 1] if i + 1 < len(tokens) else ""
        if prev == "@" or (prev == "." and before not in {"this", "super"}):
            continue
        if (i == first_call or prev in {"val", "var", "fun"} or (typed(prev) and after in _DECLARED_BEFORE)
                or (prev in {"(", ","} and after == ":" and language.colon_types)
                or (prev == "(" and before == "for") or _lambda_parameter(tokens, i)):
            declared.add(t)
        else:
            used.add(t)
    return sorted(used - declared - names.implicit - imported(imports))
