"""The guide's targets step: <device>/targets.yaml from the resolved apps.targets, after the device folder is known and
before any model step; and the stop each path entry that is no app ends with."""
from __future__ import annotations

import yaml

from .. import run_dir as rd
from ..app.facts.path_id import path_id
from ..app.facts.target_set import MISSING, Skipped
from ..files import write_text
from ..stop import Halt, halt_of
from .state import Guide


def write_targets(g: Guide) -> str:
    if g.target_set is None:
        return "--app runs one app; no targets.yaml"
    path = write_text(g.device / rd.TARGETS, yaml.safe_dump(g.target_set.document(), sort_keys=False))
    return f"{path}: {len(g.target_set.apps)} apps, {len(g.target_set.skipped)} skipped"


def refused(s: Skipped) -> tuple[str, Halt]:
    """A path entry's app id and its stop: no folder is target_missing, any other non-app not_android_project."""
    app = path_id(s.path)
    if s.kind == MISSING:
        return app, halt_of("target_missing", f"{s.path} is no folder; its earlier results stay", stage="guide",
                            step="target", app=app)
    return app, halt_of("not_android_project", f"{s.path}: {s.kind} ({s.reason})", stage="guide", step="target", app=app)
