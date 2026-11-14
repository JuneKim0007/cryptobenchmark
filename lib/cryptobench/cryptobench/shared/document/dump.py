"""dump_yaml: a value as YAML text through one named profile, the option set whose bytes its writer has always written."""
from __future__ import annotations

from types import MappingProxyType

import yaml

BLOCK = MappingProxyType({"sort_keys": False})
FLOW_LEAVES = MappingProxyType({**BLOCK, "default_flow_style": None})
WIDE = MappingProxyType({**BLOCK, "width": 200})
UNICODE = MappingProxyType({**BLOCK, "allow_unicode": True})
WIDE_UNICODE = MappingProxyType({**UNICODE, "width": 200})


def dump_yaml(doc, profile: MappingProxyType = BLOCK) -> str:
    return yaml.safe_dump(doc, **profile)
