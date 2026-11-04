from __future__ import annotations

import json


def parse_object(text: str) -> tuple[dict | None, list[str]]:
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        return None, [f"reply is not JSON: {e}"]
    if not isinstance(d, dict):
        return None, ["reply is not an object"]
    return d, []
