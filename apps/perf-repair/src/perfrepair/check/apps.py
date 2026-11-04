"""Each app's dossiers.json the replay checks, against its scopes, units, the groups and the app's screen verdicts."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.screen import Verdict
from ..dto.site import Scope
from ..dto.unit import read_units
from ..files import read_json
from ..screen.catalog import Catalog
from ..validation.dossiers.against_run import validate_dossiers
from ..validation.dossiers.units import validate_dossier_units


def check_dossiers(run: Path, groups: dict, screen: dict[int, Verdict] | None, catalog: Catalog) -> dict[str, list[str]]:
    out, handler = {}, catalog.handler()
    for directory in sorted(run.glob(f"*/{rd.DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in rd.read_scopes(directory.parent / rd.SCOPES)["scopes"]]
        verdicts = handler.app_verdicts(groups, screen, read_json(directory.parent / rd.APP).get("targetSdk"))
        doc = read_json(directory)
        units = read_units(read_json(directory.parent / rd.UNITS))
        out[str(directory.relative_to(run))] = (validate_dossiers(doc, scopes, groups, verdicts)
                                                + validate_dossier_units(doc, units, scopes, groups))
    return out
