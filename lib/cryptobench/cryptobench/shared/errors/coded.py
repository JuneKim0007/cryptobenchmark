"""The code a failure carries: the code word its message starts with, or its `.code` field; Coded marks a failure that carries one."""
from __future__ import annotations

import re
from functools import cached_property

# a code holds an underscore, or is one word before a colon: prose such as "pipeline exited 1" is none
CODE = re.compile(r"^(?:([a-z][a-z0-9]*_[a-z0-9_]+)\b|([a-z]+):)")


def code_in(text: str) -> str | None:
    found = CODE.match((text or "").strip())
    return (found.group(1) or found.group(2)) if found else None


def code_of(e: BaseException) -> str | None:
    code = getattr(e, "code", None)
    return code if isinstance(code, str) else None


class Coded(Exception):
    """A failure whose message is its own coded line; Coded adds no ValueError base."""

    # a `.code` set by the class or its __init__ wins over this reading of the message
    @cached_property
    def code(self) -> str | None:
        return code_in(str(self))

