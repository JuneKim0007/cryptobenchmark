"""Every stop, warn and skip code once, as the glossary lists them: its default action, the actions `stops.<code>` may
choose (none: fixed), exit code and next step."""
from __future__ import annotations

from cryptobench.shared.errors.glossary import Code, stops

CODES_LIST: tuple[Code, ...] = stops()
CODES: dict[str, Code] = {c.code: c for c in CODES_LIST}
OVERRIDABLE = tuple(c for c in CODES_LIST if not c.fixed)
