"""The answer's JSON schema, for structured output. Every field required; empty strings mean "not given",
which keeps the schema within what structured output accepts without nullable unions."""
from ....validation.answer_text import NOT_BLANK, or_empty
from ....validation.parse.grouping_assign import MAX_DESCRIPTION, SLUG

ID = {"type": "string", "pattern": SLUG.pattern}
ID_OR_EMPTY = {"type": "string", "pattern": or_empty(SLUG.pattern)}

SCHEMA = {
    "type": "object",
    "properties": {
        "group": ID_OR_EMPTY,
        "newGroup": {"type": "object",
                     "properties": {"id": ID_OR_EMPTY,
                                    "description": {"type": "string", "maxLength": MAX_DESCRIPTION}},
                     "required": ["id", "description"], "additionalProperties": False},
        "amend": {"type": "array", "items": {
            "type": "object",
            "properties": {"group": ID,
                           "description": {"type": "string", "maxLength": MAX_DESCRIPTION, "pattern": NOT_BLANK}},
            "required": ["group", "description"], "additionalProperties": False}},
        "reason": {"type": "string", "pattern": NOT_BLANK},
    },
    "required": ["group", "newGroup", "amend", "reason"],
    "additionalProperties": False,
}
