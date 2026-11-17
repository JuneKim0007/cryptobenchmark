"""session.yaml read and checked whole: a file that cannot be read stops; a target's order and files are judged per target when resolved."""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from cryptobench.shared.document.document import AT_PATH, DocumentKind
from cryptobench.shared.errors.input_error import InputError

SESSION_DOC = DocumentKind("session", 1, AT_PATH)
HOST = "host"
SELECT = ("all", "listed")
TOP = ("schemaVersion", "name", "devices", "host", "defaults", "targets")
SECTIONS = {"devices": ("emulators", "select"), "host": ("benchmark",), "defaults": ("config", "suites", "order")}
TARGET = ("config", "suites", "order")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclasses.dataclass(frozen=True)
class Session:
    path: Path
    name: str
    emulators: bool
    select: str
    host_benchmark: bool
    # config, suites, order as written; paths resolved against the session file's folder
    defaults: dict
    targets: dict[str, dict]


def refused(path, code, detail):
    return InputError(f"{code}: {path}: {detail}", path)


def keys(path, where, value, known):
    if not isinstance(value, dict):
        raise refused(path, "not_a_mapping", f"{where} is a {type(value).__name__}")
    unknown = sorted(set(value) - set(known))
    if unknown:
        raise refused(path, "unknown_keys", f"{where} [{', '.join(map(str, unknown))}], known [{', '.join(known)}]")
    return value


def entry(path, where, value, folder):
    """config and suites typed and resolved; order left as written for the target's own check."""
    value = keys(path, where, value or {}, TARGET)
    out = dict(value)
    if "config" in value:
        if not isinstance(value["config"], str) or not value["config"].strip():
            raise refused(path, "wrong_type", f"{where}.config is {value['config']!r}; expected a file path")
        out["config"] = (folder / value["config"]).resolve()
    if "suites" in value:
        suites = value["suites"]
        if not isinstance(suites, list) or not all(isinstance(s, str) and s.strip() for s in suites):
            raise refused(path, "wrong_type", f"{where}.suites is {suites!r}; expected a list of test-set file paths")
        out["suites"] = [(folder / s).resolve() for s in suites]
    return out


def flag(path, where, value, default):
    if value is None:
        return default
    if not isinstance(value, bool):
        raise refused(path, "wrong_type", f"{where} is {value!r}; expected true or false")
    return value


def parse(path: Path) -> Session:
    path = Path(path)
    if not path.is_file():
        raise InputError(f"missing_file: {path} (session)", path)
    doc = keys(path, "session", SESSION_DOC.read(path), TOP)
    folder = path.resolve().parent
    devices, host = (keys(path, section, doc.get(section) or {}, SECTIONS[section]) for section in ("devices", "host"))
    select = devices.get("select", "all")
    if select not in SELECT:
        raise refused(path, "wrong_type", f"devices.select is {select!r}; expected all or listed")
    name = doc.get("name", path.stem)
    if not isinstance(name, str) or not NAME.match(name):
        raise refused(path, "wrong_type", f"name is {name!r}; expected letters, digits, '.', '_' or '-'")
    targets = doc.get("targets") or {}
    if not isinstance(targets, dict):
        raise refused(path, "not_a_mapping", f"targets is a {type(targets).__name__}")
    return Session(path=path.resolve(), name=name, emulators=flag(path, "devices.emulators", devices.get("emulators"), False), select=select,
                   host_benchmark=flag(path, "host.benchmark", host.get("benchmark"), False),
                   defaults=entry(path, "defaults", doc.get("defaults"), folder),
                   targets={str(t): entry(path, f"targets.{t}", v, folder) for t, v in targets.items()})
