"""dossiers.json into the replace stage's Dossiers and noOptions, by the checks of validation/dossiers.py."""
from __future__ import annotations

from collections import Counter

from ...dto.site import Dossier
from ..dossiers import check_dossier, check_header, check_no_options


def parse_dossiers(doc: dict, app: str) -> tuple[list[Dossier], dict[str, str], list[str]]:
    """The dossiers, each noOptions scope with its reason code, and every problem found."""
    problems = check_header(doc)
    if problems:
        return [], {}, problems
    if doc["app"] != app:
        return [], {}, [f"dossiers are for app {doc['app']!r}, not {app!r}"]
    problems = check_no_options(doc)
    dossiers = []
    for raw in doc["dossiers"]:
        d, found = check_dossier(raw, app)
        problems += found
        if d is not None:
            dossiers.append(d)
    none = {n["scope"]: n["reason"] for n in doc["noOptions"] if isinstance(n, dict) and "scope" in n}
    keys = Counter([d.key for d in dossiers] + [n.get("scope") for n in doc["noOptions"] if isinstance(n, dict)])
    problems += [f"{k}: scope appears more than once" for k, n in sorted(keys.items(), key=str) if n > 1]
    return dossiers, none, problems
