"""Whether init runs before every use of an operation, derived from an entry as one build sees it and the glossary's directions and roles."""
from __future__ import annotations

from .algorithms import ROW_SECTIONS
from .glossary import direction_of, lives

PER_USE, NEVER, FORWARD = "perUse", "never", "forward"


def reinit(view: dict, operation: str) -> str:
    """view: view_for's entry; a build's own rows decide, so a base with no perUse row says nothing of a build that has one."""
    if direction_of(operation) != FORWARD:
        return NEVER
    held = {row["name"] for section in ROW_SECTIONS for row in view[section]}
    return PER_USE if any(lives(role, FORWARD) == PER_USE for role in held) else NEVER
