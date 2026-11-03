"""Whether the replacement decision is stable: N sampled units of a device's apps, each asked K times on its unchanged
message, every accepted pick compared free text left out → <device>/review/stability.json. Nothing is committed."""
from __future__ import annotations

import random
from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits, ask
from ..ai.runtime.prompt import PromptLibrary
from ..ai.suggest.site_replace.kind import SiteReplaceKind, charter
from ..files import write_json
from .sheet import choice

# a fixed draw, so two runs sample the same units
SEED = 1


def _units(device: Path) -> list[tuple[SiteReplaceKind, object]]:
    found = []
    for folder in rd.app_dirs(device):
        paths = rd.AppPaths(device, folder.name)
        if paths.dossiers.is_file():
            kind = SiteReplaceKind(folder.name, rd.read_dossiers(paths.dossiers), paths.root)
            found += [(kind, u) for u in kind.items()]
    return found


def stability(device: Path, conversations: Conversations, library: PromptLibrary, sample: int, asks: int,
              limits: Limits = Limits()) -> dict:
    units = _units(Path(device))
    chosen = random.Random(SEED).sample(units, min(sample, len(units)))
    rows = []
    for kind, u in chosen:
        picks = []
        for _ in range(asks):
            asked = ask(conversations, charter(library), kind.render(u, kind.empty()), lambda t: kind.check(u, t, None), limits)
            picks.append(choice(asked.decision) if asked.decision is not None else None)
        rows.append({"app": kind.app, "unit": u.key, "picks": picks, "stable": None not in picks and len(set(picks)) == 1})
    doc = {"sample": len(rows), "asks": asks, "stable": sum(r["stable"] for r in rows), "units": rows}
    rd.review_stability(device).parent.mkdir(parents=True, exist_ok=True)
    write_json(rd.review_stability(device), doc)
    return doc
