from __future__ import annotations

import re

from cryptobench.paths import GroupingTree
from cryptobench.catalogue.names import NAME_CONFLICT
from ..dto.classify import Answer
from .. import run_dir as rd
from cryptobench.catalogue.grouping import Item, read_items
from ..dto.screen import (ACCEPTED, MODEL_SOURCE, MODEL_STATUS, STATUSES, UNKNOWN, UNVERIFIED, Verdict, read_screen,
                          read_screen_built, read_screen_catalog, read_screen_review)
from ..files import read_json
from .failure import require

SHA256 = re.compile(r"[0-9a-f]{64}")


def _model_source_problem(v: Verdict, review: str | None) -> str:
    if not (v.source or "").startswith(MODEL_SOURCE):
        return ""
    if review is None:
        return f"{v.status} from {v.source}, but screen.json records no review"
    if v.source != MODEL_SOURCE + review:
        return f"{v.status} from {v.source}, but screen.json was reviewed under {review}"
    return ""


def _verdict_problems(n: int, v: Verdict, review: str | None) -> list[str]:
    model = _model_source_problem(v, review)
    checks = ((bool(model), model),
              (v.status not in STATUSES, f"status {v.status!r} is not one of {list(STATUSES)}"),
              (not v.reason, "no reason"),
              (v.status != UNKNOWN and not v.source, f"{v.status} without a source"),
              (v.status in STATUSES and v.status != ACCEPTED and not v.canonical and not v.reason.startswith(NAME_CONFLICT),
               f"{v.status} without the canonical name it was screened by"),
              (v.status == UNVERIFIED and not (v.source or "").startswith(MODEL_SOURCE), "unverified without a model source"))
    return [f"{n}: {text}" for failed, text in checks if failed]


def validate_screen(verdicts: dict[int, Verdict], items: list[Item], review: str | None = None) -> list[str]:
    """review: the classify outbox fingerprint; a model-sourced verdict must name exactly it."""
    ids = {i.id for i in items}
    problems = [f"{n}: no verdict" for n in sorted(ids - set(verdicts))]
    problems += [f"{n}: verdict for no item" for n in sorted(set(verdicts) - ids)]
    return problems + [p for n, v in sorted(verdicts.items()) for p in _verdict_problems(n, v, review)]


def _catalog_problems(catalog) -> list[str]:
    ok = isinstance(catalog, dict) and isinstance(catalog.get("source"), str) and catalog["source"] != "" \
        and isinstance(catalog.get("sha256"), str) and SHA256.fullmatch(catalog["sha256"])
    return [] if ok else [f"catalog {catalog!r} is not {{source, sha256}}"]


def _built_problems(recorded, built: dict) -> list[str]:
    if not isinstance(recorded, dict):
        return [f"built {recorded!r} is not {{items, profiles}}"]
    return [f"built from another {name}.json (sha256 {str(recorded.get(name))[:12]}), this run's is "
            f"{str(built.get(name))[:12]}; rerun grouping build" for name in ("items", "profiles")
            if recorded.get(name) != built.get(name) or built.get(name) is None]


def validate_screen_document(doc: dict, items: list[Item], built: dict) -> list[str]:
    """built: the digests of this run's items.json and profiles.json (run_dir.built); another build's verdicts are refused."""
    try:
        verdicts, catalog, recorded = read_screen(doc), read_screen_catalog(doc), read_screen_built(doc)
        review = read_screen_review(doc)
    except (KeyError, TypeError, ValueError) as e:
        return [f"screen.json does not parse: {e}"]
    problems = _built_problems(recorded, built)
    return problems + _catalog_problems(catalog) + ([] if problems else validate_screen(verdicts, items, review))


def read_checked_screen(paths: GroupingTree) -> dict[int, Verdict] | None:
    """screen.json's verdicts, refused unless valid and built with this run's items and profiles; None without it."""
    if not paths.screen.exists():
        return None
    try:
        doc, items = read_json(paths.screen), read_items(read_json(paths.items))
    except (OSError, KeyError, TypeError, ValueError) as e:
        require("grouping/screen.json", [f"does not read: {e}"])
    require("grouping/screen.json", validate_screen_document(doc, items, rd.built(paths)))
    return read_screen(doc)


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
