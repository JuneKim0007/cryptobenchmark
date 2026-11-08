"""A value against its JSON schema: every problem with its path. The schema is an answer's one source of its shape."""
from __future__ import annotations

import re

TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


def _type(value, want: str) -> bool:
    # a bool is an int in Python, never in JSON
    return isinstance(value, TYPES[want]) and not (want in ("integer", "number") and isinstance(value, bool))


def _object(value: dict, schema: dict, at: str) -> list[str]:
    props = schema.get("properties", {})
    found = [f"{at}{k} is missing" for k in schema.get("required", []) if k not in value]
    if schema.get("additionalProperties") is False:
        found += [f"{at}{k} is not a field here (fields: {', '.join(props) or 'none'})" for k in value if k not in props]
    return found + [p for k, v in value.items() if k in props for p in walk(v, props[k], f"{at}{k}.")]


def _string(value: str, schema: dict, at: str) -> list[str]:
    where, found = at[:-1] or "the answer", []
    if len(value) > schema.get("maxLength", len(value)):
        found.append(f"{where} is longer than {schema['maxLength']} characters")
    if len(value) < schema.get("minLength", 0):
        found.append(f"{where} is shorter than {schema['minLength']} characters")
    if "pattern" in schema and re.search(schema["pattern"], value) is None:
        found.append(f"{where} {value!r} does not match {schema['pattern']}")
    return found


def walk(value, schema: dict, at: str = "") -> list[str]:
    where = at[:-1] or "the answer"
    if "enum" in schema and value not in schema["enum"]:
        return [f"{where} {value!r} is not one of {schema['enum']}"]
    want = schema.get("type")
    if want is not None and not _type(value, want):
        return [f"{where} is not a{'n' if want[0] in 'aeiou' else ''} {want}"]
    if want == "object":
        return _object(value, schema, at)
    if want == "array":
        found = [f"{where} holds {len(value)}, at most {schema['maxItems']}"] if len(value) > schema.get("maxItems", len(value)) else []
        return found +[p for n, v in enumerate(value) for p in walk(v, schema.get("items", {}), f"{at[:-1]}[{n}].")]
    return _string(value, schema, at) if want == "string" else []
