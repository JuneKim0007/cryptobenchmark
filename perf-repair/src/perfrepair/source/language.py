"""The source languages perf-repair reads and edits: one row of lexical facts each."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    name: str
    suffix: str
    script_suffix: str | None
    terminators: str
    template: str
    nested_comments: bool
    colon_types: bool

    @property
    def newline_ends_statement(self) -> bool:
        return "\n" in self.terminators


JAVA = Language("java", ".java", None, ";", "", nested_comments=False, colon_types=False)
KOTLIN = Language("kotlin", ".kt", ".kts", ";\n", "$", nested_comments=True, colon_types=True)
LANGUAGES = (JAVA, KOTLIN)
NAMES = tuple(lang.name for lang in LANGUAGES)
SOURCE_SUFFIXES = tuple(lang.suffix for lang in LANGUAGES)


def of_file(name: str) -> Language | None:
    suffix = os.path.splitext(name)[1]
    return next((lang for lang in LANGUAGES if lang.suffix == suffix), None)


def of_build_file(name: str) -> Language:
    """Groovy and properties build files are lexed by Java's comment and string rules."""
    suffix = os.path.splitext(name)[1]
    return next((lang for lang in LANGUAGES if lang.script_suffix == suffix), JAVA)
