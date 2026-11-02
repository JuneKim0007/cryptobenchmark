from ....dto.worthiness import DECISIONS
from ....validation.answer_text import NOT_BLANK, alias_pattern
from ....validation.evaluate.worthiness import MEMBER_PREFIX

MEMBER = {"type": "string", "pattern": alias_pattern(MEMBER_PREFIX)}

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "pairs": {"type": "array", "items": {
            "type": "object",
            "properties": {"from": MEMBER, "to": MEMBER, "reason": {"type": "string", "pattern": NOT_BLANK}},
            "required": ["from", "to", "reason"],
            "additionalProperties": False,
        }},
        "reason": {"type": "string", "pattern": NOT_BLANK},
    },
    "required": ["decision", "pairs", "reason"],
    "additionalProperties": False,
}
