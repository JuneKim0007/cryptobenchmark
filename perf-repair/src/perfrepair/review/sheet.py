"""<device>/review/decisions.tsv: one row per model decision with the code facts beside it; a rebuild keeps what a person filled."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.engine.outbox import active_outbox
from ..dto.decision import OutboxRecord
from ..dto.grouping import read_items, read_profiles
from ..dto.site import Dossier
from ..files import read_json
from ..result.gain import option_label

COLUMNS = ("kind", "app", "item", "model", "facts", "pick", "reason", "concerns", "verdict", "note")
GROUPING, REPLACE, CLASSIFY, WORTHY = "grouping", "replace", "classify", "worthiness"
KEY = ("kind", "app", "item", "pick")
FREE_TEXT = ("reason", "description")
DROPPED = "(dropped)"


@dataclass(frozen=True)
class Stage:
    """One model stage's folder; app empty for a device-level stage."""
    kind: str
    app: str
    root: Path


def stages(device: Path) -> list[Stage]:
    grouping = rd.GroupingPaths(device)
    found = [Stage(GROUPING, "", grouping.root), Stage(CLASSIFY, "", grouping.classify)]
    found += [Stage(WORTHY, mode, rd.worthiness(device, mode)) for mode in rd.worthiness_modes(device)]
    return found + [Stage(REPLACE, d.name, rd.AppPaths(device, d.name).replace) for d in rd.app_dirs(device)]


def _optional(path: Path) -> dict:
    return read_json(path) if path.is_file() else {}


def _item_facts(grouping: rd.GroupingPaths) -> dict[str, dict]:
    if not grouping.items.is_file():
        return {}
    profiles = read_profiles(_optional(grouping.profiles)) if grouping.profiles.is_file() else {}
    facts = {}
    for i in read_items(read_json(grouping.items)):
        signature = profiles[i.id].signature if i.id in profiles else None
        facts[i.key] = {"family": i.family, "signature": signature.known() if signature else None}
    return facts


def _scope_facts(paths: rd.AppPaths) -> dict[str, tuple[dict, dict]]:
    """Per scope its facts and, by item, its options' class and code label."""
    out = {}
    for raw in _optional(paths.dossiers).get("dossiers") or []:
        d = Dossier.from_json(raw)
        s = d.scope
        out[d.key] = ({"current": d.current, "sinks": list(s.sinks), "keySource": s.keySource,
                       "options": [o.item for o in d.options]},
                      {o.item: {"change": o.change, "label": option_label(o.estimates)} for o in d.options})
    return out


def choice(decision: dict) -> str:
    """What a decision picks, free text left out: the same choice in other words is the same choice."""
    return json.dumps({k: v for k, v in decision.items() if k not in FREE_TEXT}, sort_keys=True)


def _grouping_pick(decision: dict) -> str:
    return decision.get("group") or (decision.get("newGroup") or {}).get("id") or ""


def _row(stage: Stage, r: OutboxRecord, item: str, facts: dict, pick: str, reason: str, concerns=()) -> dict:
    return {"kind": stage.kind, "app": stage.app, "item": item, "model": r.agent.model or "", "facts": json.dumps(facts, sort_keys=True),
            "pick": pick, "reason": reason, "concerns": "; ".join(concerns), "verdict": "", "note": ""}


def _replace_rows(stage: Stage, r: OutboxRecord, scopes: dict[str, tuple[dict, dict]]) -> list[dict]:
    rows = []
    # a record before units decided one scope at its top level
    for one in (r.decision.get("replacements") or [r.decision]):
        facts, classes = scopes.get(one["scope"], ({}, {}))
        option = one.get("option")
        chosen = classes.get(option, {})
        rows.append(_row(stage, r, one["scope"], {**facts, **chosen}, f"{one['decision']} {option}" if option else one["decision"],
                         one.get("reason") or "", one.get("concerns") or ()))
    return rows


def _rows_of(stage: Stage, r: OutboxRecord, items: dict, scopes: dict) -> list[dict]:
    if r.decision is None:
        return [_row(stage, r, r.item, items.get(r.item, {}), DROPPED, "; ".join(r.problems))]
    if stage.kind == REPLACE:
        return _replace_rows(stage, r, scopes)
    pick = _grouping_pick(r.decision) if stage.kind == GROUPING else choice(r.decision)
    return [_row(stage, r, r.item, items.get(r.item, {}), pick, r.decision.get("reason") or "")]


def rows(device: Path) -> list[dict]:
    items = _item_facts(rd.GroupingPaths(device))
    out: list[dict] = []
    for stage in stages(device):
        scopes = _scope_facts(rd.AppPaths(device, stage.app)) if stage.kind == REPLACE else {}
        for r in active_outbox(stage.root).records():
            out += _rows_of(stage, r, items, scopes)
    return out


def risk(row: dict) -> int:
    """Riskiest first: a recommend or a trade-off chosen, then a replace, a keep, then every other kind."""
    if row["kind"] != REPLACE:
        return 3
    pick = row["pick"].split(" ", 1)[0]
    if pick == "recommend" or (pick == "replace" and json.loads(row["facts"]).get("label") == "trade_off"):
        return 0
    return 1 if pick == "replace" else 2


def read_sheet(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _key(row: dict) -> tuple:
    return tuple(row[k] for k in KEY)


def write_sheet(device: Path) -> list[dict]:
    """A decision the model changed comes back empty: the old verdict judged another pick."""
    path = rd.review_sheet(device)
    filled = {_key(r): r for r in read_sheet(path)}
    built = [{**r, "verdict": filled[_key(r)]["verdict"], "note": filled[_key(r)]["note"]} if _key(r) in filled else r
             for r in sorted(rows(device), key=risk)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(built)
    return built
