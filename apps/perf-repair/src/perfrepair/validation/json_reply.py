from __future__ import annotations

import json

from .schema_walk import walk


def parse_object(text: str) -> tuple[dict | None, list[str]]:
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [f"reply is not JSON: {e}"]
    if not isinstance(d, dict):
        return None, ["reply is not an object"]
    return d, []


def check_reply(text: str, schema: dict) -> tuple[dict | None, list[str]]:
    """The reply as an object when its schema holds, else every problem; a job's checks come after."""
    d, problems = parse_object(text)
    problems = problems or walk(d, schema)
    return (None, problems) if problems else (d, [])
