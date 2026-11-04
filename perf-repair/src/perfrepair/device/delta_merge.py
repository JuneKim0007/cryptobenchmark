"""Add-only merge of a delta's cases into the stored benchmark: every changed file is written new beside the old one, and
manifest.yaml, renamed in last, is the one switch, so an interrupted merge leaves the stored benchmark whole."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..dto.dossier import SETUP_DRIFT
from ..files import json_text, read_json, read_yaml, write_text_making_parents
from ..stop.halt import Coded

PLANNED = ("prepared", "skipped")


@dataclass(frozen=True)
class Merged:
    added: tuple[str, ...]
    folder: str


def _tag(cases: list[dict], session: str, comparison: str) -> list[dict]:
    return [{**c, "session": session, **({"sessionDrift": True} if comparison == SETUP_DRIFT else {})} for c in cases]


def _added(stored: list[dict], delta: list[dict], ids: set[str], session: str, comparison: str) -> list[dict]:
    present = {c["id"] for c in stored}
    clash = sorted(ids & present)
    if clash:
        raise Coded(f"merge_refused: {', '.join(clash)} already in the stored benchmark; a merge only adds")
    return stored + _tag([c for c in delta if c["id"] in ids], session, comparison)


def _benchmarks(stored: dict, delta: dict, ids: set[str], session: str, comparison: str) -> dict:
    return {**stored, "cases": _added(stored.get("cases") or [], delta.get("cases") or [], ids, session, comparison)}


def _plan_file(key: str, stored: dict, delta: dict) -> dict:
    """prepared and skipped: the delta's entries the stored file lacks; a lost case is planned there already."""
    field = "cases" if key == "prepared" else "skipped"
    have = stored.get(field) or []
    known = {c.get("id") for c in have} if key == "prepared" else {repr(c) for c in have}
    new = [c for c in delta.get(field) or [] if (c.get("id") if key == "prepared" else repr(c)) not in known]
    return {**stored, field: have + new}


def _same_repetitions(stored: dict, delta: dict) -> None:
    mine, theirs = len(stored["files"].get("processes") or ()), len(delta["files"].get("processes") or ())
    if mine != theirs:
        raise Coded(f"merge_refused: unequal_repetitions: the stored benchmark has {mine} process files, the delta {theirs}")


def merge_delta(folder: Path, staged: Path, ids: set[str], session: str, comparison: str, retried=()) -> Merged:
    """ids: the delta's cases to add; one already stored refuses the merge, never replaces a case; retried: the lost cases
    this delta measured again, whether or not they came back."""
    folder, staged = Path(folder), Path(staged)
    manifest, delta = read_yaml(folder / rd.MANIFEST), read_yaml(staged / rd.MANIFEST)
    _same_repetitions(manifest, delta)
    out = Path("benchmark") / f"merged-{session}"
    files = dict(manifest["files"])
    texts = {"benchmark": json_text(_benchmarks(read_json(folder / files["benchmark"]),
                                                read_json(staged / delta["files"]["benchmark"]), ids, session, comparison))}
    for n, (mine, theirs) in enumerate(zip(files.get("processes") or (), delta["files"].get("processes") or ()), 1):
        texts[f"process-{n}"] = json_text(_benchmarks(read_json(folder / mine), read_json(staged / theirs), ids, session, comparison))
    for key in PLANNED:
        if files.get(key) and delta["files"].get(key):
            texts[key] = yaml.safe_dump(_plan_file(key, read_yaml(folder / files[key]), read_yaml(staged / delta["files"][key])),
                                        sort_keys=False)
    for key, text in texts.items():
        name = f"{key}/benchmark.json" if key.startswith("process-") else f"{key}.yaml" if key in PLANNED else "benchmark.json"
        write_text_making_parents(folder / out / name, text)
    files.update({k: str(out / (f"{k}.yaml" if k in PLANNED else "benchmark.json")) for k in texts if not k.startswith("process-")})
    if files.get("processes"):
        files["processes"] = [str(out / f"process-{n}/benchmark.json") for n in range(1, len(files["processes"]) + 1)]
    counts = dict(manifest.get("counts") or {})
    counts["measured"] = counts.get("measured", 0) + len(ids)
    if "prepared" in texts:
        counts["prepared"] = len(yaml.safe_load(texts["prepared"]).get("cases") or [])
    deltas = list(manifest.get("deltas") or []) + [{"session": session, "cases": sorted(ids), "comparison": comparison,
                                                     "from": str(staged)}]
    tried = sorted(set(manifest.get("retried") or ()) | set(retried))
    write_text_making_parents(folder / rd.MANIFEST, yaml.safe_dump({**manifest, "files": files, "counts": counts, "deltas": deltas,
                                                                    **({"retried": tried} if tried else {})}, sort_keys=False))
    return Merged(tuple(sorted(ids)), str(out))
