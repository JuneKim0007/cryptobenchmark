"""Whole lines of a source file: a function's line range and its import lines."""
from __future__ import annotations

from ...source.language import Language
from ...source.lexer import line_starts, mask


def function_lines(text: str, start: int, end: int) -> str:
    """Lines `start..end`, 1-based inclusive; edits keep line numbers, so one range serves both copies."""
    starts = line_starts(text)
    return text[starts[start - 1]:starts[end] if end < len(starts) else len(text)]


def import_lines(text: str, language: Language) -> list[str]:
    masked = mask(text, language).splitlines()
    return [line.strip() for line, code in zip(text.splitlines(), masked) if code.lstrip().startswith("import ")]
