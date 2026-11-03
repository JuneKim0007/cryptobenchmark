from ....dto.gaps import CANDIDATE_PREFIX, GAP_PREFIX, UNKNOWN_CHOICE, USE_ORIGINS
from ....dto.lifecycle import ORIGINS
from ....validation.answer_text import alias_pattern

SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {"type": "array", "items": {
            "type": "object",
            "properties": {"gap": {"type": "string", "pattern": alias_pattern(GAP_PREFIX)},
                           "choice": {"type": "string",
                                      "pattern": f"^{UNKNOWN_CHOICE}$|{alias_pattern(CANDIDATE_PREFIX)}"},
                           "origin": {"type": "string", "enum": list(dict.fromkeys(ORIGINS + USE_ORIGINS))}},
            "required": ["gap", "choice", "origin"],
            "additionalProperties": False,
        }},
    },
    "required": ["answers"],
    "additionalProperties": False,
}
