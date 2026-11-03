"""The parts of a trial's `resolved` text that fix the function; the rest (IV, tag, sizes) the call chooses."""
from __future__ import annotations

from functools import lru_cache

from ..catalog.names import Names

DIGEST_ENGINE = "MessageDigest"
FUNCTION_FIXED = ("digest", "mgf1")


@lru_cache(maxsize=1)
def _names() -> Names:
    return Names.load()


def digest_name(text: str) -> str:
    return _names().canonical(DIGEST_ENGINE, text).name.upper()


def function_parameters(resolved: str | None) -> tuple[tuple[str, str], ...]:
    """Each value by its canonical digest name: providers report one digest under different spellings."""
    pairs = (token.split("=", 1) for token in (resolved or "").split() if "=" in token)
    return tuple(sorted((k.lower(), digest_name(v))
                        for k, v in pairs if k.lower() in FUNCTION_FIXED))
