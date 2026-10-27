from __future__ import annotations

_ESCAPES = {"java": {"\\": "\\\\", '"': '\\"'}, "kotlin": {"\\": "\\\\", '"': '\\"', "$": "\\$"}}


def string_literal(value: str, language: str) -> str:
    if any(ch in value for ch in "\n\r"):
        raise ValueError(f"{value!r}: a line break in a rendered literal")
    return '"' + "".join(_ESCAPES[language].get(ch, ch) for ch in value) + '"'
