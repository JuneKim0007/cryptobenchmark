"""A session's targets against the devices adb lists: each resolved or skipped with one coded line, never stopping the others; order groups."""
from __future__ import annotations

import collections
import dataclasses
import itertools
from pathlib import Path
from typing import Callable

from cryptobench.shared.device.probe import EMULATOR, DeviceRow
from cryptobench.shared.errors.input_error import InputError
from cryptobench.shared.session.document import HOST, Session


@dataclasses.dataclass(frozen=True)
class TargetSpec:
    name: str
    key: str
    # the adb serial a worker gets as ANDROID_SERIAL; None on the host
    transport: str | None
    config: Path
    suites: tuple[Path, ...]
    order: int
    unstable: bool = False
    # layers over config: defaults' overlays, then the target's
    overlays: tuple[Path, ...] = ()


@dataclasses.dataclass(frozen=True)
class Resolved:
    targets: list[TargetSpec]
    # (target, coded line)
    skipped: list[tuple[str, str]]
    notices: list[str]


def find(name: str, rows: list[DeviceRow], aliases: dict[str, str]) -> DeviceRow | None:
    """Exact key, then alias, then transport serial; no prefix or pattern match."""
    for wanted, field in ((name, "key"), (aliases.get(name), "key"), (name, "transport")):
        found = [row for row in rows if wanted and getattr(row, field) == wanted]
        if found:
            return found[0]
    return None


def order_of(name: str, entry: dict, defaults: dict, fallback: int | None) -> int | str:
    """The order or the invalid_order line; fallback when neither entry nor defaults set one (the host's after-phones)."""
    value = entry["order"] if "order" in entry else defaults.get("order", 0) if fallback is None else fallback
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return f"invalid_order: {name}: {value!r}; use an integer >= 0"
    return value


def files_of(name: str, entry: dict, defaults: dict, config: Callable[[], Path]) -> tuple[Path, tuple[Path, ...], tuple[Path, ...]] | str:
    """The target's config, suites and overlays, or the line that skips it; a named file that is missing never falls back. config replaces,
    overlays append."""
    named = entry.get("config") or defaults.get("config")
    chosen = named or config()
    if not chosen.is_file():
        where = f"targets.{name}.config" if entry.get("config") else "defaults.config"
        return f"missing_file: {chosen} ({where})"
    overlays = (*defaults.get("overlays", []), *entry.get("overlays", []))
    for overlay in overlays:
        if not overlay.is_file():
            return f"missing_file: {overlay} (overlays of {name})"
    suites = entry.get("suites", defaults.get("suites", []))
    if not suites:
        return f"nothing_to_measure: {name}: no suites in targets.{name} or defaults"
    for suite in suites:
        if not suite.is_file():
            return f"missing_file: {suite} (suites of {name})"
    stems = collections.defaultdict(list)
    for suite in suites:
        stems[suite.stem].append(suite)
    clash = next((paths for paths in stems.values() if len(paths) > 1), None)
    if clash:
        return f"target_conflict: {name}: suites {', '.join(map(str, clash))} share the name {clash[0].stem}"
    return chosen, tuple(suites), overlays


def resolve(session: Session, rows: list[DeviceRow], aliases: dict[str, str], config: Callable[[], Path]) -> Resolved:
    """config() is the run's own global.yaml chain, asked only when neither the target nor defaults name one."""
    skipped, notices, devices = [], [], {}
    for name, entry in session.targets.items():
        if name == HOST:
            continue
        row = find(name, rows, aliases)
        if row is None:
            attached = ", ".join(r.key for r in rows) or "none"
            skipped.append((name, f"device_not_attached: {name}: adb lists no such key, alias or serial; attached: {attached}"))
        elif not row.ready:
            skipped.append((name, row.reason))
        else:
            devices.setdefault(row.key, []).append((name, entry, row))
    if session.select == "all":
        for row in rows:
            if row.ready and row.key not in devices and (session.emulators or row.kind != EMULATOR):
                devices[row.key] = [(row.key, {}, row)]
    targets = []
    for key, named in devices.items():
        if len(named) > 1:
            names = " and ".join(n for n, _, _ in named)
            skipped += [(n, f"target_conflict: {names} name one device, {key}") for n, _, _ in named]
            continue
        name, entry, row = named[0]
        order, files = order_of(name, entry, session.defaults, None), files_of(name, entry, session.defaults, config)
        problem = next((value for value in (order, files) if isinstance(value, str)), None)
        if problem:
            skipped.append((name, problem))
            continue
        targets.append(TargetSpec(name, key, row.transport, files[0], files[1], order, row.note is not None, files[2]))
    if not session.host_benchmark:
        notices.append("host_benchmark_not_set: host.benchmark is false")
        if HOST in session.targets:
            skipped.append((HOST, "host_benchmark_not_set: host.benchmark is false"))
    else:
        entry = session.targets.get(HOST, {})
        after_phones = max((t.order for t in targets), default=-1) + 1
        order, files = order_of(HOST, entry, session.defaults, None if "order" in entry else after_phones), files_of(HOST, entry, session.defaults, config)
        problem = next((value for value in (order, files) if isinstance(value, str)), None)
        if problem:
            skipped.append((HOST, problem))
        else:
            targets.append(TargetSpec(HOST, HOST, None, files[0], files[1], order, overlays=files[2]))
    return Resolved(targets, skipped, notices)


def groups(targets: list[TargetSpec]) -> list[list[TargetSpec]]:
    """Ascending order; one group's targets share an order value."""
    ordered = sorted(targets, key=lambda t: t.order)
    return [list(group) for _, group in itertools.groupby(ordered, key=lambda t: t.order)]


def nothing_to_measure(resolved: Resolved) -> InputError | None:
    if resolved.targets:
        return None
    host = "; host.benchmark is false" if resolved.notices else ""
    return InputError(f"nothing_to_measure: no device target is ready or resolved{host}")
