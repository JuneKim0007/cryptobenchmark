"""StageContext, what each stage of one run reads, and Stage, the shape of a stage."""
from __future__ import annotations

import argparse
import dataclasses
import pathlib
from collections.abc import Callable


@dataclasses.dataclass(frozen=True)
class StageContext:
    """device is the runner's Device or None, typed object because cryptobench imports no app;
    checked is the parse-only check's answer for configuration, None on a run that starts no build."""
    options: argparse.Namespace
    configuration: pathlib.Path
    device: object
    checked: dict | None = None
    problems: list[str] = dataclasses.field(default_factory=list)


Stage = Callable[[StageContext], object]
