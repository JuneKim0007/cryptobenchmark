"""The answer's JSON schema, for structured output. Every field required; "" and [] mean "not given",
which keeps the schema within what structured output accepts without nullable unions."""
from ....dto.site import DECISIONS, EDIT_KINDS, OPTION_PREFIX, RISKS
from ....validation.answer_text import NOT_BLANK, alias_pattern, or_empty

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "option": {"type": "string", "pattern": or_empty(alias_pattern(OPTION_PREFIX))},
        "edits": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(EDIT_KINDS)},
                "provider": {"type": "string"},
                "algorithm": {"type": "string"},
                "parameters": {"type": "array", "items": {
                    "type": "object", "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                    "required": ["name", "value"], "additionalProperties": False}},
            },
            "required": ["kind", "provider", "algorithm", "parameters"],
            "additionalProperties": False,
        }},
        "risks": {"type": "array", "items": {"type": "string", "enum": list(RISKS)}},
        "reason": {"type": "string", "pattern": NOT_BLANK},
    },
    "required": ["decision", "option", "edits", "risks", "reason"],
    "additionalProperties": False,
}
