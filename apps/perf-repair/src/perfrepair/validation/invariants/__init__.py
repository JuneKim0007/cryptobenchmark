"""The grouping and scoping invariants of a device folder: one list of findings, for the command and the guide's gate."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ... import run_dir as rd
from ...dto.pattern import FIXED, INIT_AND_OPERATION
from ...dto.site import Scope
from ...dto.unit import read_units
from ...files import read_json
from ...run_dir import GroupingPaths
from ..boundary import boundary_violations
from ..finding import UNDECIDED, Violation
from ..grouping.invariants import Grouping, grouping_invariants
from ..scoping.invariants import scoping_invariants
from ..scoping.source import Sources


def _absent(files: tuple[Path, ...], subject: str) -> list[Violation]:
    return [Violation("inputs_present", UNDECIDED, subject, (str(f),), "rerun the step that writes it; the rules that read it did not run")
            for f in files if not f.is_file()]


def _grouping_absent(device: Path) -> list[Violation]:
    paths = GroupingPaths(device)
    return _absent((paths.groups, paths.profiles, paths.checks), "grouping")


def load_grouping(device: Path) -> Grouping | None:
    paths = GroupingPaths(device)
    if not paths.groups.is_file() or not paths.profiles.is_file():
        return None
    checks = read_json(paths.checks)["findings"] if paths.checks.is_file() else []
    screen = rd.load_screen(paths) or {}
    return Grouping(read_json(paths.groups), read_json(paths.profiles)["profiles"], checks,
                    {str(i): v.canonical for i, v in screen.items()})


def source_root(app: Path, apps: Path | None, root: Path | None = None) -> Path | None:
    """app.json's root and projectRoot; apps: a folder holding the app trees, when they moved since the run; root: the
    app's own tree, as the guide was given it."""
    facts = read_json(app / rd.APP) if (app / rd.APP).is_file() else {}
    if not facts.get("root"):
        return None
    root = root or (Path(facts["root"]) if apps is None else apps / Path(facts["root"]).name)
    return root / (facts.get("projectRoot") or ".")


def init_per_call(device: Path) -> frozenset[tuple[str, str]]:
    """rows.json's (type, algorithm) whose fixed rows all redo init per call; none without rows.json."""
    if not (device / rd.ROWS).is_file():
        return frozenset()
    seen: dict[tuple[str, str], set] = defaultdict(set)
    for r in read_json(device / rd.ROWS)["rows"]:
        if r.get("variant") == FIXED:
            seen[(r["type"], r["algorithm"])].add(r.get("perCall"))
    return frozenset(k for k, per_call in seen.items() if per_call == {INIT_AND_OPERATION})


def app_violations(app: Path, apps: Path | None = None, per_call: frozenset[tuple[str, str]] = frozenset(),
                   root: Path | None = None) -> list[Violation]:
    scopes_file, units_file = app / rd.SCOPES, app / rd.UNITS
    if not scopes_file.is_file():
        return _absent((scopes_file,), app.name)
    scopes = [Scope.from_json(s) for s in rd.read_scopes(scopes_file)["scopes"]]
    units = read_units(read_json(units_file)) if units_file.is_file() else []
    return scoping_invariants(scopes, units, Sources(source_root(app, apps, root)), per_call)


def _dossiers(device: Path, only: str | None = None) -> dict[str, dict]:
    return {a.name: read_json(a / rd.DOSSIERS) for a in rd.app_dirs(device)
            if (a / rd.DOSSIERS).is_file() and only in (None, a.name)}


def run_invariants(device: Path, apps: Path | None = None, against: Path | None = None) -> list[Violation]:
    device = Path(device)
    found = _grouping_absent(device)
    g = load_grouping(device)
    if g is not None:
        other = load_grouping(Path(against)) if against is not None else None
        found += grouping_invariants(g, _dossiers(device), other)
    found += boundary_violations(device)
    per_call = init_per_call(device)
    for app in rd.app_dirs(device):
        found += app_violations(app, apps, per_call)
    return found


def _touched(g: Grouping, doc: dict) -> set[str]:
    group_of = {e["qualified"]: e["group"] for e in g.groups["items"].values()}
    names = {d.get("current") for d in doc.get("dossiers") or []}
    names |= {o.get("item") for d in doc.get("dossiers") or [] for o in d.get("options") or []}
    return {group_of[n] for n in names if group_of.get(n)}


def app_gate(device: Path, app: str, root: Path) -> list[Violation]:
    """What the guide checks before an app's replace step: the groups its dossiers draw from, and its own scopes read
    from root."""
    device = Path(device)
    found = _grouping_absent(device)
    g = load_grouping(device)
    dossiers = _dossiers(device, app)
    if g is not None and app in dossiers:
        touched = {f"group {gid}" for gid in _touched(g, dossiers[app])}
        found += [v for v in grouping_invariants(g, dossiers) if v.subject.startswith(app + " ") or touched & set(v.evidence)]
    found += boundary_violations(device)
    return found + app_violations(rd.app_dir(device, app), None, init_per_call(device), root)
