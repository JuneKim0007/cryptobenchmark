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


def _tag(case: dict, session: str, comparison: str) -> dict:
    return {**case, "session": session, **({"sessionDrift": True} if comparison == SETUP_DRIFT else {})}


def _filled(case: dict, theirs: dict | None, metrics, session: str, comparison: str) -> dict:
    """The delta's runs of the metrics the stored case lacks, beside its own untouched; the case reads as the delta's
    session, so a comparison through it says cross_session."""
    new = {m: theirs["metrics"][m] for m in metrics if theirs and m in theirs["metrics"] and m not in case["metrics"]}
    if not new:
        return case
    return _tag({**case, "metrics": {**case["metrics"], **new}, "filled": sorted(new)}, session, comparison)


def _added(stored: list[dict], delta: list[dict], ids: set[str], fill: dict, session: str, comparison: str) -> list[dict]:
    present = {c["id"] for c in stored}
    clash = sorted(ids & present)
    if clash:
        raise Coded(f"merge_refused: {', '.join(clash)} already in the stored benchmark; a merge only adds")
    theirs = {c["id"]: c for c in delta}
    kept = [_filled(c, theirs.get(c["id"]), fill.get(c["id"], ()), session, comparison) for c in stored]
    return kept + [_tag(c, session, comparison) for c in delta if c["id"] in ids]


def _benchmarks(stored: dict, delta: dict, ids: set[str], fill: dict, session: str, comparison: str) -> dict:
    return {**stored, "cases": _added(stored.get("cases") or [], delta.get("cases") or [], ids, fill, session, comparison)}


def _plan_file(key: str, stored: dict, delta: dict) -> dict:
    """prepared and skipped: the delta's entries the stored file lacks; a lost case is planned there already."""
    field = "cases" if key == "prepared" else "skipped"
    have = stored.get(field) or []
    known = {c.get("id") for c in have} if key == "prepared" else {repr(c) for c in have}
    new = [c for c in delta.get(field) or [] if (c.get("id") if key == "prepared" else repr(c)) not in known]
    return {**stored, field: have + new}


def _samples(docs: list[dict]) -> dict[tuple[str, str, str], tuple[int, ...]]:
    """Per (item, case, metric) its run count in each document: the merged benchmark first, then each process file."""
    out: dict[tuple[str, str, str], list[int]] = {}
    for n, doc in enumerate(docs):
        for c in doc.get("cases") or []:
            item = f"{c.get('type')}|{c.get('algorithm')}|{c.get('provider')}"
            for m, v in (c.get("metrics") or {}).items():
                out.setdefault((item, c["id"], m), [0] * len(docs))[n] = len(v.get("runs") or ())
    return {k: tuple(v) for k, v in out.items()}


def _same_samples(mine: dict, theirs: dict, merged: set[str]) -> None:
    """A shared case is held to its own counts, an added or filled one to the stored cases' of its item and metric."""
    by_item: dict[tuple[str, str], set] = {}
    for (item, _, m), counts in mine.items():
        by_item.setdefault((item, m), set()).add(counts)
    for (item, cid, m), counts in sorted(theirs.items(), key=lambda kv: kv[0][1:]):
        expected = {mine[item, cid, m]} if (item, cid, m) in mine else by_item.get((item, m)) if cid in merged else None
        if expected and counts not in expected:
            what = "per process" if {c[0] for c in expected} == {counts[0]} else "runs"
            raise Coded(f"merge_refused: unequal_samples: {cid}.{m}: {what} {list(counts)} in the delta, "
                        f"{min(map(list, expected))} stored")


def merge_delta(folder: Path, staged: Path, ids: set[str], session: str, comparison: str, retried=(),
                fill: dict | None = None) -> Merged:
    """ids: the delta's cases to add; one already stored refuses the merge, never replaces a case; retried: the lost cases
    this delta measured again; fill: per stored case the metrics it lacks, taken from the delta's same case."""
    folder, staged, fill = Path(folder), Path(staged), fill or {}
    manifest, delta = read_yaml(folder / rd.MANIFEST), read_yaml(staged / rd.MANIFEST)
    files = dict(manifest["files"])
    mine = [read_json(folder / p) for p in [files["benchmark"], *(files.get("processes") or ())]]
    theirs = [read_json(staged / p) for p in [delta["files"]["benchmark"], *(delta["files"].get("processes") or ())]]
    _same_samples(_samples(mine), _samples(theirs), ids | set(fill))
    out = Path("benchmark") / f"merged-{session}"
    merged = _benchmarks(mine[0], theirs[0], ids, fill, session, comparison)
    texts = {"benchmark": json_text(merged)}
    for n, (a, b) in enumerate(zip(mine[1:], theirs[1:]), 1):
        texts[f"process-{n}"] = json_text(_benchmarks(a, b, ids, fill, session, comparison))
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
    filled = {c["id"]: c["filled"] for c in merged["cases"] if c["id"] in fill and c.get("session") == session and c.get("filled")}
    deltas = list(manifest.get("deltas") or []) + [{"session": session, "cases": sorted(ids), "comparison": comparison,
                                                     "from": str(staged), **({"filled": filled} if filled else {})}]
    tried = sorted(set(manifest.get("retried") or ()) | set(retried))
    write_text_making_parents(folder / rd.MANIFEST, yaml.safe_dump({**manifest, "files": files, "counts": counts, "deltas": deltas,
                                                                    **({"retried": tried} if tried else {})}, sort_keys=False))
    return Merged(tuple(sorted(ids)), str(out))
