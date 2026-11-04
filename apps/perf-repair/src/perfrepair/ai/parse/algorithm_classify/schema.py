from ....dto.classify import ANSWERS
from ....validation.answer_text import NOT_BLANK

SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "answer": {"type": "string", "enum": list(ANSWERS)},
                           "reason": {"type": "string", "pattern": NOT_BLANK}},
            "required": ["id", "answer", "reason"],
            "additionalProperties": False,
        }},
    },
    "required": ["answers"],
    "additionalProperties": False,
}
