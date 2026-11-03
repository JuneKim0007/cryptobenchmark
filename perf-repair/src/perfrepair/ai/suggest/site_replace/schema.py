"""The answer's JSON schema, for structured output. Every field required; [] means "not given", which keeps the schema
within what structured output accepts without nullable unions."""
from ....dto.metrics import NAMES
from ....dto.site import DECISIONS, EDIT_KINDS, MAX_CONCERN_LENGTH, MAX_CONCERNS, OPTION_PREFIX, RISKS
from ....dto.unit import MEMBER_PREFIX
from ....validation.answer_text import NOT_BLANK, alias_pattern

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "members": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "member": {"type": "string", "pattern": alias_pattern(MEMBER_PREFIX)},
                "option": {"type": "string", "pattern": alias_pattern(OPTION_PREFIX)},
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
                "needs": {"type": "array", "items": {"type": "string", "pattern": NOT_BLANK}},
            },
            "required": ["member", "option", "edits", "risks", "needs"],
            "additionalProperties": False,
        }},
        "deciding": {"type": "array", "items": {"type": "string", "enum": list(NAMES)}},
        "accepted": {"type": "array", "items": {"type": "string", "enum": list(NAMES)}},
        "concerns": {"type": "array", "maxItems": MAX_CONCERNS,
                     "items": {"type": "string", "pattern": NOT_BLANK, "maxLength": MAX_CONCERN_LENGTH}},
        "reason": {"type": "string", "pattern": NOT_BLANK},
    },
    "required": ["decision", "members", "deciding", "accepted", "concerns", "reason"],
    "additionalProperties": False,
}
