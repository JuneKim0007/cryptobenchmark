from ....validation.review.grouping_review import KINDS

SCHEMA = {
    "type": "object",
    "properties": {"findings": {"type": "array", "items": {
        "type": "object",
        "properties": {"kind": {"type": "string", "enum": list(KINDS)},
                       "groups": {"type": "array", "items": {"type": "string"}},
                       "items": {"type": "array", "items": {"type": "integer"}},
                       "reason": {"type": "string"}},
        "required": ["kind", "groups", "items", "reason"], "additionalProperties": False}}},
    "required": ["findings"],
    "additionalProperties": False,
}
