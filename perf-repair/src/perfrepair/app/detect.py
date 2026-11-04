"""The detect step: an app's non-test sources → JCA call sites, constants folded, import-checked, resolved."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable

from ..source.code import Code
from .find.constants import Constants
from .facts.dependencies import Registration, registrations
from .facts.gate import AppRoot
from .find.imports import import_reason
from .find.scan import Argument, Site, call_pattern, provider_inner, scan
from .find.sources import TEST, skipped_copies, source_files


@dataclass
class Detection:
    sites: list[dict] = field(default_factory=list)
    dropped: list[dict] = field(default_factory=list)
    registers: list[Registration] = field(default_factory=list)
    files: int = 0
    testFiles: int = 0
    folded: int = 0
    skippedCopies: int = 0


def _fold(arg: Argument | None, constants: Constants, provider: bool, at: int) -> Argument | None:
    if arg is None or arg.literal is not None:
        return arg
    expr = provider_inner(arg.expr) if provider and provider_inner(arg.expr) is not None else arg.expr
    value = constants.fold(expr, at=at)
    return arg if value is None else Argument(arg.expr, value, folded=True)


def fold(site: Site, constants: Constants) -> Site:
    return replace(site, algorithm=_fold(site.algorithm, constants, False, site.offset),
                   provider=_fold(site.provider, constants, True, site.offset))


def detect(app: AppRoot, engine_types: set[str], resolve: Callable[[Site], dict]) -> Detection:
    """resolve: the site against the device's primitives (resolve.Primitives); detection itself reads no device data."""
    out, pattern = Detection(skippedCopies=skipped_copies(app.path)), call_pattern(engine_types)
    for f in source_files(app.path):
        if f.origin == TEST:
            out.testFiles += 1
            continue
        out.files += 1
        code = Code.of(f.path.read_text(errors="replace"), f.language)
        out.registers += registrations(code, f.rel)
        if pattern is None:
            continue
        constants = None
        for site in scan(code, f.rel, f.origin, pattern):
            reason = import_reason(code, site.engineType, site.offset)
            if reason is not None:
                out.dropped.append({"file": site.file, "line": site.line, "engineType": site.engineType,
                                    "call": site.call, "reason": reason})
                continue
            constants = constants or Constants(code)
            folded = fold(site, constants)
            out.folded += folded != site
            out.sites.append(resolve(folded))
    return out
