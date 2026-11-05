"""catalog/role-contracts.yaml: what each AI role is told, may read and may write, read and checked whole."""
from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path

import yaml

from ..dto.coded import InputError
from ..dto.document import AT_PATH, DocumentKind

CATALOG = Path(__file__).with_name("role-contracts.yaml")
SCHEMA_VERSION = 1
ROW_FIELDS = {"prompt", "schema", "charter", "folder", "required", "optional", "tools", "writes"}
LISTS = ("required", "optional", "tools", "writes")
PIN = re.compile(r"[0-9a-f]{12}")
SLOT = re.compile(r"\{(app|mode)\}")
# the engine's files in every role's folder and the log every command writes; never a role's input
ENGINE_FILES = ("journal.jsonl", "errors.jsonl", "writes.json", "outbox/active", "outbox/*/charter.json", "outbox/*/[0-9]*.json")
LOG_FILES = "log/*"


class ContractError(InputError):
    pass


CONTRACTS_DOC = DocumentKind("role contracts", SCHEMA_VERSION, "contracts_invalid: " + AT_PATH, ContractError)


@dataclass(frozen=True)
class RoleContract:
    role: str
    prompt: str
    schema: str
    charter: str
    folder: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    tools: tuple[str, ...]
    writes: tuple[str, ...]

    def bind(self, **names) -> "RoleContract":
        """The row at one app or mode: its slots filled."""
        fill = lambda p: SLOT.sub(lambda m: names[m[1]], p)
        return RoleContract(self.role, self.prompt, self.schema, self.charter, fill(self.folder),
                            tuple(map(fill, self.required)), tuple(map(fill, self.optional)), self.tools,
                            tuple(map(fill, self.writes)))

    def folders_glob(self) -> str:
        return SLOT.sub("*", self.folder)

    def names_of(self, folder: str) -> dict[str, str]:
        """The slots' values of a folder this row's glob found."""
        return re.fullmatch(SLOT.sub(lambda m: f"(?P<{m[1]}>[^/]+)", self.folder), folder).groupdict()

    def bookkeeping(self, path: str) -> bool:
        """The engine's own files and the log: read and written by every role, feeding no message."""
        return fnmatchcase(path, LOG_FILES) or any(fnmatchcase(path, f"{self.folder}/{p}") for p in ENGINE_FILES)

    def may_write(self, path: str) -> bool:
        return self.bookkeeping(path) or any(fnmatchcase(path, p) for p in self.writes)

    def declares(self, path: str) -> bool:
        return any(fnmatchcase(path, p) for p in (*self.required, *self.optional))

    def required_missing(self, files: list[str]) -> list[str]:
        return [p for p in self.required if not any(fnmatchcase(f, p) for f in files)]


def _problems(role: str, raw: dict) -> list[str]:
    missing, stray = ROW_FIELDS - set(raw), set(raw) - ROW_FIELDS
    if missing or stray:
        return [f"{role}: missing {sorted(missing)}, unknown {sorted(stray)}"]
    found = [f"{role}: {k} is not a list" for k in LISTS if not isinstance(raw[k], list)]
    found += [f"{role}: charter {raw['charter']!r} is not 12 hex digits"] * (not PIN.fullmatch(str(raw["charter"])))
    if found:
        return found
    both = sorted(set(raw["required"]) & set(raw["optional"]))
    return [f"{role}: {both} both required and optional"] * bool(both) + [f"{role}: no required input"] * (not raw["required"])


def load(path: Path = CATALOG) -> dict[str, RoleContract]:
    doc = yaml.safe_load(Path(path).read_text())
    CONTRACTS_DOC.check(doc, path)
    problems = [p for role, raw in doc["roles"].items() for p in _problems(role, raw)]
    if problems:
        raise ContractError("contracts_invalid: " + "; ".join(problems))
    return {role: RoleContract(role, raw["prompt"], raw["schema"], raw["charter"], raw["folder"], tuple(raw["required"]),
                               tuple(raw["optional"]), tuple(raw["tools"]), tuple(raw["writes"]))
            for role, raw in doc["roles"].items()}


@cache
def role_contracts() -> dict[str, RoleContract]:
    return load()
