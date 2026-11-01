from ....dto.worthiness import DECISIONS

SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "pairs": {"type": "array", "items": {
            "type": "object",
            "properties": {"from": {"type": "string"}, "to": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["from", "to", "reason"],
            "additionalProperties": False,
        }},
        "reason": {"type": "string"},
    },
    "required": ["decision", "pairs", "reason"],
    "additionalProperties": False,
}
