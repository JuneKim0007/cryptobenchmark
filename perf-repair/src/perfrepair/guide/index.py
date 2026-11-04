"""<device>/apps-index.tsv: one line per app folder, joined from its files and the run's guide events, so an app can be
found later and what is left to do on it read: python3 -m perfrepair.guide.index --device-results <device>."""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from .. import run_dir as rd
from ..app.facts.project import gradle_name
from ..config.device_results import add_device_results_arg, fill_device_results
from ..dto.change import CHANGES, TRACKS
from ..dto.event import END
from ..dto.pattern import PATTERNS, UNKNOWN_DEFAULT
from ..failure import reported
from ..files import read_json, write_text
from ..log import attach
from ..log.read import read_events

# the step an app reached: the last of an unbroken run of files in guide order, each no older than the one before
STAGES = (("app", rd.SCOPES), ("dossier", rd.DOSSIERS), ("replace", rd.REPLACEMENTS), ("edit", rd.EDITS),
          ("harness", rd.HARNESS), ("device", f"{rd.MEASURED}/{rd.SCOPED_BENCHMARK}"), ("report", rd.REPORT))
ORDER = [name for name, _ in STAGES]
COLUMNS = ("app", "project", "source", "sites", "scopes", *PATTERNS, UNKNOWN_DEFAULT, "stage", "stop", "reason", *CHANGES,
           *TRACKS, "notOffered", "replace", "measured")


def _stops(device: Path) -> dict[str, tuple[str, str]]:
    """Each app's stop in its latest guide run, (code, reason); an app whose latest run stopped nowhere has none."""
    events = Path(device) / rd.EVENTS
    latest: dict[str, tuple[str, str, str]] = {}
    for e in read_events(events) if events.is_file() else []:
        if e.stage != "guide" or not e.app or e.event != END or e.step == "target":
            continue
        if e.outcome == "stop":
            latest[e.app] = (e.run, e.data.get("code", ""), e.detail.partition(": ")[2])
        elif e.app not in latest or latest[e.app][0] != e.run:
            latest[e.app] = (e.run, "", "")
    return {app: (code, reason) for app, (_, code, reason) in latest.items()}


def _stage(folder: Path) -> str:
    """A file a later step left from an earlier run is older than the one rewritten before it, so it does not count."""
    reached, since = "", 0.0
    for name, file in STAGES:
        path = folder / file
        if not path.exists() or path.stat().st_mtime < since:
            break
        reached, since = name, path.stat().st_mtime
    return reached


def _count(path: Path, key: str) -> int | str:
    return len(read_json(path)[key]) if path.is_file() else ""


def _patterns(path: Path) -> dict:
    """Scopes per category and those the default put there; blank without scopes.json."""
    scopes = read_json(path)["scopes"] if path.is_file() else None
    if scopes is None:
        return {k: "" for k in (*PATTERNS, UNKNOWN_DEFAULT)}
    return {**{p: sum(s["pattern"] == p for s in scopes) for p in PATTERNS},
            UNKNOWN_DEFAULT: sum(s["patternReason"] == UNKNOWN_DEFAULT for s in scopes)}


def _reached(stage: str, step: str) -> bool:
    return bool(stage) and ORDER.index(stage) >= ORDER.index(step)


def _row(folder: Path, project: str, stops: dict) -> dict:
    """A column read from a later step's file counts only when the reached stage covers that step."""
    paths, facts = rd.AppPaths(folder.parent, folder.name), read_json(folder / rd.APP)
    stage = _stage(folder)
    dossiers = read_json(paths.dossiers) if _reached(stage, "dossier") else {"dossiers": [], "notOffered": []}
    options = [o for d in dossiers["dossiers"] for o in d["options"]]
    changes, tracks = Counter(o.get("change", "drop-in") for o in options), Counter(o.get("track") for o in options)
    chosen = read_json(paths.replacements)["replacements"] if _reached(stage, "replace") else []
    code, reason = stops.get(folder.name, ("", ""))
    return {"app": folder.name, "project": project, "source": facts["root"], "sites": _count(paths.sites, "sites"),
            "scopes": _count(paths.scopes, "scopes"), **_patterns(paths.scopes), "stage": stage, "stop": code, "reason": reason,
            **{c: changes[c] for c in CHANGES}, **{t: tracks[t] for t in TRACKS},
            "notOffered": len(dossiers["notOffered"]), "replace": sum(r["decision"] == "replace" for r in chosen),
            "measured": "yes" if _reached(stage, "device") else "no"}


def _cell(value) -> str:
    return " ".join(str(value).split())


def _project(root: str, common: str | None) -> str:
    """Two trees of one folder name, as two `android` checkouts, differ by their path under the apps' common folder."""
    return gradle_name(root) or (os.path.relpath(root, common) if common else Path(root).name)


def write_index(device: Path) -> Path:
    roots = {f: read_json(f / rd.APP)["root"] for f in rd.app_dirs(device)}
    common = os.path.commonpath(list(roots.values())) if len(roots) > 1 else None
    stops = _stops(device)
    rows = [_row(f, _project(r, common), stops) for f, r in roots.items()]
    lines = ["\t".join(COLUMNS)] + ["\t".join(_cell(r[c]) for c in COLUMNS) for r in rows]
    return write_text(Path(device) / rd.APPS_INDEX, "\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = argparse.ArgumentParser(prog="perfrepair.guide.index", description=__doc__)
    add_device_results_arg(ap)
    a = ap.parse_args(argv)
    return reported(lambda: _index(ap, a))


def _index(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    fill_device_results(ap, a)
    print(write_index(a.device_results))


if __name__ == "__main__":
    sys.exit(main())
