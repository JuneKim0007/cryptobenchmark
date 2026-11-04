"""engines.yaml read and checked once: each engine type's lifecycle calls, and the origin table every slice shares."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto.document import AT_PATH, DocumentKind
from ..dto.lifecycle import ORIGINS, REQUIREMENTS
from ..files import read_yaml

ENGINES = Path(__file__).with_name("engines.yaml")
SUPPORTED_SCHEMA = 1
ENGINES_DOC = DocumentKind("engines", SUPPORTED_SCHEMA, AT_PATH)
_ENGINE_KEYS = {"configuration", "terminal", "optional", "requirements", "operations", "consumers"}
_TOP_KEYS = {"schemaVersion", "factory", "engines", "origins", "specs", "accessors", "decoders"}


@dataclass(frozen=True)
class Engine:
    """by_call: call → operation; by_argument: (call, index, argument value → operation)."""
    configuration: frozenset[str]
    terminal: frozenset[str]
    optional: frozenset[str]
    requirements: dict[str, dict[int, str]]
    by_call: dict[str, str]
    by_argument: tuple[str, int, dict[str, str]] | None
    consumers: frozenset[str]

    def role(self, call: str) -> str:
        if call in self.terminal:
            return "use"
        return "configure" if call in self.configuration or call in self.optional else "other"


@dataclass(frozen=True)
class Engines:
    factory: str
    engines: dict[str, Engine]
    origins: dict[str, frozenset[str]]
    specs: dict[str, int]
    accessors: frozenset[str]
    decoders: frozenset[str]

    def origin_of_call(self, name: str) -> str | None:
        return next((o for o in ORIGINS if name in self.origins.get(o, ())), None)


def _problems(name: str, raw: dict) -> list[str]:
    out = [f"{name}: unknown keys {sorted(set(raw) - _ENGINE_KEYS)}"] if set(raw) - _ENGINE_KEYS else []
    if not raw.get("terminal"):
        out.append(f"{name}: no terminal calls")
    calls = set(raw.get("configuration") or ()) | set(raw.get("terminal") or ()) | set(raw.get("optional") or ())
    for call, args in (raw.get("requirements") or {}).items():
        if call not in calls:
            out.append(f"{name}: requirement call {call} is not a lifecycle call")
        bad = [v for k, v in args.items() if not isinstance(k, int) or v not in REQUIREMENTS]
        if bad:
            out.append(f"{name}: requirements of {call} {bad} are not index → one of {REQUIREMENTS}")
    return out + _operation_problems(name, raw.get("operations") or {}, calls)


def _operation_problems(name: str, ops: dict, calls: set[str]) -> list[str]:
    out = [f"{name}: operations is one of call or argument"] if set(ops) - {"call", "argument"} or len(ops) > 1 else []
    if "call" in ops and set(ops["call"]) - calls:
        out.append(f"{name}: operations name calls {sorted(set(ops['call']) - calls)} outside its lifecycle")
    arg = ops.get("argument")
    if arg is not None and (arg.get("call") not in calls or not isinstance(arg.get("index"), int)):
        out.append(f"{name}: operations argument needs a lifecycle call and an integer index")
    return out


def _engine(raw: dict) -> Engine:
    ops = raw.get("operations") or {}
    arg = ops.get("argument")
    return Engine(frozenset(raw.get("configuration") or ()), frozenset(raw["terminal"]), frozenset(raw.get("optional") or ()),
                  {c: dict(a) for c, a in (raw.get("requirements") or {}).items()}, dict(ops.get("call") or {}),
                  (arg["call"], arg["index"], {str(k): v for k, v in arg["values"].items()}) if arg else None,
                  frozenset(raw.get("consumers") or ()))


@cache
def read_engines(path: Path = ENGINES) -> Engines:
    doc = read_yaml(path)
    ENGINES_DOC.check(doc, path)
    problems = [f"unknown keys {sorted(set(doc) - _TOP_KEYS)}"] if set(doc) - _TOP_KEYS else []
    problems += [p for name, raw in (doc.get("engines") or {}).items() for p in _problems(name, raw)]
    problems += [f"origin {o} is not one of {ORIGINS}" for o in doc.get("origins") or {} if o not in ORIGINS]
    if not isinstance(doc.get("factory"), str):
        problems.append("factory is not a call name")
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return Engines(doc["factory"], {n: _engine(r) for n, r in doc["engines"].items()},
                   {o: frozenset(v) for o, v in doc["origins"].items()}, dict(doc["specs"]),
                   frozenset(doc["accessors"]), frozenset(doc["decoders"]))
