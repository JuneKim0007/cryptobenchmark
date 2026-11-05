"""The answer's JSON schema: one alias and a reason; there is no answer that keeps the current algorithm."""
from ....dto.dossier import OPTION_PREFIX
from ....validation.answer_text import NOT_BLANK, alias_pattern

SCHEMA = {
    "type": "object",
    "properties": {
        "option": {"type": "string", "pattern": alias_pattern(OPTION_PREFIX)},
        "reason": {"type": "string", "pattern": NOT_BLANK},
    },
    "required": ["option", "reason"],
    "additionalProperties": False,
}
