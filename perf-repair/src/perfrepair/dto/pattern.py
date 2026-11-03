"""The two divergence categories: a scope's pattern, the benchmark variant that measures it, and each rule's words."""
from __future__ import annotations

FIXED, NOT_FIXED = "fixed", "notFixed"
PATTERNS = (FIXED, NOT_FIXED)
# a benchmark case without a variant predates them: the one variant it measured is notFixed
VARIANTS, LEGACY_VARIANT = PATTERNS, NOT_FIXED
CREATED_PER_CALL, HELD_IN_FIELD, UNKNOWN_DEFAULT = "created_per_call", "held_in_field", "unknown_default"
# reason → (the pattern it gives, the rule in plain words)
PATTERN_RULES = {
    CREATED_PER_CALL: (NOT_FIXED, "the function that creates the object uses it, so every call pays the setup"),
    HELD_IN_FIELD: (FIXED, "a field holds the object, created outside the methods that use it one method away"),
    UNKNOWN_DEFAULT: (NOT_FIXED, "the reading leaves open where the setup runs, so the default applies"),
}
PATTERN_REASONS = tuple(PATTERN_RULES)


def pattern_of_reason(reason: str) -> str:
    return PATTERN_RULES[reason][0]


def rule_words(reason: str) -> str:
    return PATTERN_RULES[reason][1]
