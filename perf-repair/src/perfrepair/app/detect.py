"""The detect step: an app's non-test sources → JCA call sites, constants folded, import-checked, resolved."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..data_handler.inbound.probe_index import ProbeIndex
from ..dto import ProviderEntry
from .constants import Constants
from .dependencies import Registration, registrations
from .gate import AppRoot
from .imports import import_reason
from .lexer import Code
from .resolve import resolve
from .scan import Argument, Site, call_pattern, provider_inner, scan
from .sources import TEST, source_files


@dataclass
class Detection:
    sites: list[dict] = field(default_factory=list)
    dropped: list[dict] = field(default_factory=list)
    registers: list[Registration] = field(default_factory=list)
    files: int = 0
    testFiles: int = 0
    folded: int = 0


def _fold(arg: Argument | None, constants: Constants, provider: bool) -> Argument | None:
    if arg is None or arg.literal is not None:
        return arg
    expr = provider_inner(arg.expr) if provider and provider_inner(arg.expr) is not None else arg.expr
    value = constants.fold(expr)
    return arg if value is None else Argument(arg.expr, value, folded=True)


def fold(site: Site, constants: Constants) -> Site:
    return replace(site, algorithm=_fold(site.algorithm, constants, False),
                   provider=_fold(site.provider, constants, True))


def detect(app: AppRoot, index: ProbeIndex, providers: list[ProviderEntry]) -> Detection:
    out, pattern = Detection(), call_pattern(index.engine_types)
    for f in source_files(app.path):
        if f.origin == TEST:
            out.testFiles += 1
            continue
        out.files += 1
        code = Code.of(f.path.read_text(errors="replace"), f.kotlin)
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
            out.sites.append(resolve(folded, index, providers))
    return out
