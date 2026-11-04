"""The import lines a function needs: the names its text uses, in any variant; a wildcard only while a name stays unresolved."""
from __future__ import annotations

import re

from ..source.language import Language
from ..source.lexer import mask
from .dependencies import Names, imported_name, tokens

_WILDCARD = re.compile(r"import\s+(?:static\s+)?[\w.]+\*")
# the wrapper drops a header's annotations, so their imports would only break the compile
_ANNOTATION = re.compile(r"@[\w.]+")


def _uses(function: str, language: Language, names: Names) -> set[str]:
    head, brace, body = mask(function, language).partition("{")
    found = tokens(_ANNOTATION.sub(" ", head) + brace + body)
    return {t for i, t in enumerate(found) if names.extensions or not i or found[i - 1] != "."}


def used_imports(imports: list[str], functions: list[str], language: Language, names: Names, unresolved: list[str]) -> list[str]:
    """`unresolved`: the functions' dependencies; a wildcard cannot be read by name, so only they can justify one."""
    uses = set().union(*(_uses(f, language, names) for f in functions))

    def needed(line: str) -> bool:
        if _WILDCARD.match(line):
            return bool(unresolved)
        name = imported_name(line)
        return name in uses or name in names.conventions
    return [line for line in imports if needed(line)]
