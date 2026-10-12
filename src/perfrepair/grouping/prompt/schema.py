"""The answer's JSON schema, for structured output. Every field required; empty strings mean "not given",
which keeps the schema within what structured output accepts without nullable unions."""

SCHEMA = {
    "type": "object",
    "properties": {
        "group": {"type": "string"},
        "newGroup": {"type": "object", "properties": {"id": {"type": "string"}, "description": {"type": "string"}},
                     "required": ["id", "description"], "additionalProperties": False},
        "amend": {"type": "array", "items": {
            "type": "object", "properties": {"group": {"type": "string"}, "description": {"type": "string"}},
            "required": ["group", "description"], "additionalProperties": False}},
        "reason": {"type": "string"},
    },
    "required": ["group", "newGroup", "amend", "reason"],
    "additionalProperties": False,
}
