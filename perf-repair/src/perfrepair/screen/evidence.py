"""The items no catalog row decides, with the evidence the classify model sees, in fixed-size batches."""
from __future__ import annotations

from ..data_handler.inbound import RunContext
from ..dto.classify import Batch, Evidence
from ..dto.grouping import Item
from ..dto.screen import UNKNOWN, Verdict

BATCH = 10


def _trial(context: RunContext) -> dict[tuple, dict]:
    return {(s["provider"], s["type"], s["algorithm"]): s for s in context.trial["services"]}


def unknown_evidence(context: RunContext, items: list[Item], verdicts: dict[int, Verdict]) -> list[Evidence]:
    """Only unknown items with a canonical name: a name_conflict has no key a verdict could be recorded by."""
    trial, out = _trial(context), []
    for i in items:
        v = verdicts[i.id]
        if v.status != UNKNOWN or v.canonical is None:
            continue
        key = (i.provider, i.type, i.name)
        service = trial.get(key, {})
        error = service.get("error") or (service.get("defaultRun") or {}).get("error")
        out.append(Evidence(i.id, i.type, i.name, v.canonical, i.provider, i.family, bool(service.get("instantiates")),
                            error, context.probe.class_name(*key), dict(context.probe.attributes(*key))))
    return out


def batches(evidence: list[Evidence], size: int = BATCH) -> list[Batch]:
    return [Batch(tuple(evidence[n:n + size])) for n in range(0, len(evidence), size)]
