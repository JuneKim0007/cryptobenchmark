"""One site's lifecycle: the created object bound, its calls in the site's method and one method away, the values
those calls need, the operations they perform, and the status that follows."""
from __future__ import annotations

from dataclasses import dataclass, field

from ...dto.lifecycle import Lifecycle, Requirement, Step
from ..engines import Engine, Engines
from ..syntax.calls import Call, find_call
from ..syntax.declarations import enclosing_method, method_body
from ..syntax.resolve import resolve_field, resolve_local
from ..syntax.node import Node
from ..syntax.usage import executable_root
from .binding import Binding, bind
from .depth1 import Reach, callees, callers, field_calls, requirement_depth1
from .origins import origin
from .slice import ALIAS, PASSED, RETURN, STORED, Escape, Slice, scan, scope_calls
from .status import Found, status


@dataclass(frozen=True)
class Reading:
    """The lifecycle, and each requirement's argument it was read from."""
    lifecycle: Lifecycle
    values: dict[Requirement, Node] = field(default_factory=dict)


def _local(created: Node, name: str, method: Node | None) -> Slice:
    found = resolve_local(name, created)
    scope = found.scope if found is not None and found.scope is not None else method_body(method)
    out = scan(scope, name, created.start) if scope is not None else Slice()
    for alias in [e for e in out.escapes if e.kind == ALIAS and e.name and e.name != name]:
        out.extend(scan(scope, alias.name, alias.node.start))
    return out


def _field(created: Node, name: str, method: Node | None, reach: Reach) -> Slice:
    found = field_calls(name, created, method, reach)
    return Slice([c for c in found.calls if enclosing_method(c.node) is method], found.escapes)


def _same_method(created: Node, b: Binding, method: Node | None, reach: Reach) -> Slice:
    out = Slice(b.chain + [c for s in b.scope_calls for c in scope_calls(s)], [])
    if b.kind == "local" and b.name:
        out.extend(_local(created, b.name, method))
    elif b.kind == "field" and b.name:
        out.extend(_field(created, b.name, method, reach))
    if b.kind == "argument" and b.callee is not None:
        out.escapes.append(Escape(PASSED, b.callee.node, b.callee, b.index))
    out.escapes = [e for e in out.escapes if e.kind != ALIAS]
    return out


def _private_field(name: str | None, at: Node) -> bool:
    held = resolve_field(name, at) if name else None
    owner = held.node.parent if held is not None and held.node.parent is not None else None
    return held is not None and any(c.type == "modifiers" and "private" in c.text.split()
                                    for c in (held.node.children + (owner.children if owner is not None else [])))


def _where(names: set[str], same: list[Call], far: list[Call]) -> str | None:
    if any(c.name in names for c in same):
        return "same"
    return "depth1" if any(c.name in names for c in far) else None


def _steps(engine: Engine, same: list[Call], reach: Reach, consumed: list[Call]) -> tuple[Step, ...]:
    rows = {(engine.role(c.name), c.name, c.line, "same") for c in same}
    rows |= {(engine.role(c.name), c.name, c.line, "depth1") for c in reach.calls}
    rows |= {("consume", c.name, c.line, "same") for c in consumed}
    rows |= {("consume", c.name, c.line, "depth1") for c in reach.consumers if c.name in engine.consumers}
    return tuple(Step(*r) for r in sorted(rows, key=lambda r: (r[2], r[1], r[0], r[3])))


def _requirements(engine: Engine, calls: list[Call], engines: Engines) -> dict[Requirement, Node]:
    out: dict[Requirement, Node] = {}
    for c in calls:
        for index, name in sorted(engine.requirements.get(c.name, {}).items()):
            if index < len(c.args):
                src = origin(c.args[index], engines)
                out.setdefault(Requirement(name, src.origin, src.line, c.line, requirement_depth1(src, c.args[index], engines)),
                               c.args[index])
    return dict(sorted(out.items(), key=lambda kv: (kv[0].at, kv[0].name, kv[0].line, kv[0].origin)))


def _operations(engine: Engine, calls: list[Call]) -> tuple[str, ...]:
    ops = {engine.by_call[c.name] for c in calls if c.name in engine.by_call}
    if engine.by_argument is not None:
        call, index, values = engine.by_argument
        for c in (c for c in calls if c.name == call):
            mode = c.args[index].text.split(".")[-1].strip() if index < len(c.args) else None
            if mode not in values:
                return ()
            ops.add(values[mode])
    return tuple(sorted(ops))


def _found(b: Binding, engine: Engine, same: Slice, reach: Reach, consumed: list[Call], created: Node) -> Found:
    escapes = [e for e in same.escapes if e.kind in (RETURN, PASSED, STORED) and e.call not in consumed]
    root = executable_root(created)
    wrapped_far = any(c.name in engine.consumers for c in reach.consumers)
    configured = "same" if not engine.configuration else _where(engine.configuration, same.calls, reach.calls)
    used = "same" if consumed else _where(engine.terminal, same.calls, reach.calls)
    if used is None and wrapped_far:
        used = "depth1"
    return Found(b.kind, configured, used, bool(escapes), bool(consumed) or wrapped_far,
                 any(executable_root(c.node) is not root for c in same.calls), reach.over_budget,
                 _private_field(b.name, created) if b.kind == "field" else False)


def read_site(root: Node, site: dict, engines: Engines) -> Reading:
    engine = engines.engines.get(site["engineType"])
    if engine is None:
        return Reading(Lifecycle.unsupported("engine_unknown"))
    created = find_call(root, site["line"], site["call"], frozenset((engines.factory,)), site["engineType"])
    if created is None:
        return Reading(Lifecycle.unsupported("call_not_found"))
    method, b, reach = enclosing_method(created), bind(created), Reach()
    same = _same_method(created, b, method, reach)
    passed = [e for e in same.escapes if e.kind == PASSED and e.call is not None]
    consumed = [e.call for e in passed if e.call.name in engine.consumers]
    for helper in {id(m): m for m in [method] * (b.kind == "returned") +
                   [enclosing_method(e.node) for e in same.escapes if e.kind == RETURN]}.values():
        callers(helper, created, reach)
    callees([e for e in passed if e.call not in consumed], created, reach)
    found = _found(b, engine, same, reach, consumed, created)
    state, reasons = status(found)
    calls = same.calls + reach.calls
    values = _requirements(engine, calls, engines)
    return Reading(Lifecycle(state, reasons, b.kind, _steps(engine, same.calls, reach, consumed), tuple(values),
                             _operations(engine, calls)), values)
