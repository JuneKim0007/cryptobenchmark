from __future__ import annotations

import json

from ....dto.classify import Batch


def render(batch: Batch) -> str:
    lines = [f"PRIMITIVES ({len(batch.members)}; answer every id)"]
    for e in batch.members:
        trial = "instantiates" if e.instantiates else "does not instantiate"
        lines += ["", f"id {e.id}", f"  engine type: {e.type}", f"  name: {e.name}", f"  canonical: {e.canonical}",
                  f"  provider: {e.provider}", f"  family: {e.family}", f"  trial: {trial}; error: {e.error or 'none'}",
                  f"  className: {e.className or 'not recorded'}",
                  f"  attributes: {json.dumps(e.attributes, sort_keys=True) if e.attributes else 'none'}"]
    return "\n".join(lines)
