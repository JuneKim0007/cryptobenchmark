from ....dto.classify import ANSWERS

SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "answer": {"type": "string", "enum": list(ANSWERS)},
                           "reason": {"type": "string"}},
            "required": ["id", "answer", "reason"],
            "additionalProperties": False,
        }},
    },
    "required": ["answers"],
    "additionalProperties": False,
}
