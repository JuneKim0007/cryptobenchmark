"""The bundled step, after the targets' detect and before the benchmark: the missing set, its suggestions (written with
fromApps suggest or apply), and bundled_missing through terminate for what no applied row covers; returns the entries to apply."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml

from .. import run_dir as rd
from ..catalog.bundled_providers import BUNDLED_PROVIDERS, BundledCatalog
from ..data_handler.inbound import RunContext
from ..dto.bundled import APPLY, OFF, BundledPolicy, Suggestions
from ..dto.event import END
from ..files import write_text
from ..log import emit, step
from ..stop import CODES, terminate
from ..validation import require
from ..validation.bundled import validate_suggestions
from .bundled_config import configured
from .bundled_missing import missing_set
from .bundled_suggest import suggest

CATALOG = f"catalog/{BUNDLED_PROVIDERS.name}"


def _write(folder: Path, policy: BundledPolicy, found: Suggestions) -> Path | None:
    path = Path(folder) / rd.BUNDLED_SUGGESTIONS
    if policy.fromApps == OFF:
        path.unlink(missing_ok=True)
        return None
    doc = found.to_json(policy.fromApps, CATALOG)
    require(rd.BUNDLED_SUGGESTIONS, validate_suggestions(doc))
    return write_text(path, yaml.safe_dump(doc, sort_keys=False))


def _events(found: Suggestions, from_apps: str) -> None:
    """missing always; the catalog's verdicts only when fromApps uses the catalog."""
    kinds = () if from_apps == OFF else ("matched", "blocked", "unmatched", "applied")
    lists = {"missing": [m.provider for m in found.missing],
             **{k: [f"{s.provider} {s.artifact}" for s in getattr(found, k)] for k in kinds}}
    for kind, items in lists.items():
        if items:
            emit("device", f"bundled.{kind}", END, outcome="ok", data={"items": items})


def check_bundled(folder: Path, apps: list[str], base: Path, policy: BundledPolicy,
                  echo: Callable[[str], None] = print) -> list[dict]:
    with step("device", "bundled") as s:
        platform = RunContext.load(Path(folder) / rd.MANIFEST).probe.platform_providers()
        found = suggest(missing_set(folder, apps, platform, configured(base)), BundledCatalog.load(),
                        policy.fromApps == APPLY)
        written = _write(folder, policy, found)
        _events(found, policy.fromApps)
        s.count(**found.counts())
        if written:
            s.wrote(written)
    if written:
        echo(f"device bundled: {', '.join(f'{k} {n}' for k, n in found.counts().items())}; wrote {written}")
    left = found.left()
    if left:
        detail = "; ".join(m.text() for m in left)
        action = terminate("bundled_missing", detail, stage="device", step="bundled", data={"items": [m.provider for m in left]})
        echo(f"device bundled_missing: {action}: {detail}; {CODES['bundled_missing'].next}")
    return [a.entry for a in found.applied]
