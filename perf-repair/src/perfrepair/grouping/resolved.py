"""The parts of a trial's `resolved` text that fix the function; the rest (IV, tag, sizes) the call chooses."""
from __future__ import annotations

FUNCTION_FIXED = ("digest", "mgf1")


def function_parameters(resolved: str | None) -> tuple[tuple[str, str], ...]:
    pairs = (token.split("=", 1) for token in (resolved or "").split() if "=" in token)
    return tuple(sorted((k.lower(), v.upper()) for k, v in pairs if k.lower() in FUNCTION_FIXED))
