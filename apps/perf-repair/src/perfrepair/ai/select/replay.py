"""A Select source's file checked as written, then rebuilt from its outbox as the job projects it and compared byte for byte."""
from __future__ import annotations

from ...files import json_text, read_json
from ..runtime.engine.outbox import OutboxError, active_outbox


def replay_problems(source) -> list[str]:
    [(path, _)] = source.documents().items()
    try:
        written = source.document_problems(read_json(path))
    except (KeyError, TypeError, ValueError) as e:
        return [f"{path.name} does not parse: {e}"]
    try:
        records = active_outbox(source.folder).records()
    except OutboxError as e:
        return written + [str(e)]
    by_key = {i.key: i for i in source.items()}
    for r in records:
        item = by_key.get(r.item)
        if item is not None and r.evidence == item.evidence:
            source.apply(item, r)
    rebuilt = source.documents()[path]
    return written + source.state_problems() + (
        [] if path.read_bytes() == json_text(rebuilt).encode() else [f"{path.name} differs from the rebuild of the outbox, byte for byte"])
