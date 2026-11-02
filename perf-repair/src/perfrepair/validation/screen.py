from __future__ import annotations

import re

from ..dto.classify import Answer
from ..dto.grouping import Item
from ..dto.screen import (MODEL_SOURCE, MODEL_STATUS, NEVER_TARGET, STATUSES, UNKNOWN, UNVERIFIED, Verdict, read_screen,
                          read_screen_catalog)

SHA256 = re.compile(r"[0-9a-f]{64}")


def _verdict_problems(n: int, v: Verdict) -> list[str]:
    checks = ((v.status not in STATUSES, f"status {v.status!r} is not one of {list(STATUSES)}"),
              (not v.reason, "no reason"),
              (v.status != UNKNOWN and not v.source, f"{v.status} without a source"),
              (v.status in NEVER_TARGET and not v.canonical, f"{v.status} without the canonical name it was screened by"),
              (v.status == UNVERIFIED and not (v.source or "").startswith(MODEL_SOURCE), "unverified without a model source"))
    return [f"{n}: {text}" for failed, text in checks if failed]


def validate_screen(verdicts: dict[int, Verdict], items: list[Item]) -> list[str]:
    ids = {i.id for i in items}
    problems = [f"{n}: no verdict" for n in sorted(ids - set(verdicts))]
    problems += [f"{n}: verdict for no item" for n in sorted(set(verdicts) - ids)]
    return problems + [p for n, v in sorted(verdicts.items()) for p in _verdict_problems(n, v)]


def _catalog_problems(catalog) -> list[str]:
    ok = isinstance(catalog, dict) and isinstance(catalog.get("source"), str) and catalog["source"] != "" \
        and isinstance(catalog.get("sha256"), str) and SHA256.fullmatch(catalog["sha256"])
    return [] if ok else [f"catalog {catalog!r} is not {{source, sha256}}"]


def validate_screen_document(doc: dict, items: list[Item]) -> list[str]:
    try:
        verdicts, catalog = read_screen(doc), read_screen_catalog(doc)
    except (KeyError, TypeError, ValueError) as e:
        return [f"screen.json does not parse: {e}"]
    return _catalog_problems(catalog) + validate_screen(verdicts, items)


def validate_model_verdicts(verdicts: dict[int, Verdict], answers: dict[int, Answer], fingerprint: str) -> list[str]:
    """screen.json's model-sourced verdicts are exactly the classify answers that change a status, under one outbox."""
    problems = [p for k, v in sorted(verdicts.items()) for p in _model_problems(k, v, answers.get(k), fingerprint)]
    return problems + [f"{k}: classify answer for no item" for k in sorted(set(answers) - set(verdicts))]


def _model_problems(k: int, v: Verdict, a: Answer | None, fingerprint: str) -> list[str]:
    status = MODEL_STATUS.get(a.answer) if a else None
    if status is not None:
        same = (v.status, v.reason, v.source) == (status, a.reason, MODEL_SOURCE + fingerprint)
        return [] if same else [f"{k}: classify answered {a.answer}, screen.json says {v.status} from {v.source}"]
    if (v.source or "").startswith(MODEL_SOURCE):
        return [f"{k}: {v.status} from {v.source} without a classify answer that sets it"]
    if a is not None and v.status != UNKNOWN:
        return [f"{k}: classify answered {a.answer} for an item screened {v.status}"]
    return []
