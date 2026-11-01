from __future__ import annotations

from ...dto.language import Language


def string_literal(value: str, language: Language) -> str:
    if any(ch in value for ch in "\n\r"):
        raise ValueError(f"{value!r}: a line break in a rendered literal")
    escapes = {"\\": "\\\\", '"': '\\"'}
    if language.template:
        escapes[language.template] = "\\" + language.template
    return '"' + "".join(escapes.get(ch, ch) for ch in value) + '"'
