"""specs.yaml loaded: which JCA parameter spec a set of pinned fields names, and how each field renders."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...dto.language import Language
from ...files import read_yaml
from .literal import string_literal
from .reject import Rejected

TABLE = Path(__file__).with_name("specs.yaml")
TYPES = ("int", "string", "spec", "random_bytes", "constant")


@dataclass(frozen=True)
class Field:
    field: str
    type: str
    default: str | None = None
    cls: str | None = None


@dataclass(frozen=True)
class Spec:
    cls: str
    args: tuple[Field, ...]

    @property
    def simple_name(self) -> str:
        return self.cls.rsplit(".", 1)[-1]

    @property
    def pinnable(self) -> set[str]:
        return {f.field for f in self.args if f.type != "constant"}


@dataclass(frozen=True)
class Table:
    position: int
    encrypting_modes: tuple[str, ...]
    construct: dict
    random_bytes: dict
    specs: tuple[Spec, ...]

    def spec_for(self, fields: set[str]) -> Spec:
        if not fields:
            raise Rejected("missing_parameter")
        hits = [s for s in self.specs if fields <= s.pinnable]
        if len(hits) != 1:
            raise Rejected("unknown_parameters")
        return hits[0]

    def new(self, cls: str, args: list[str], language: Language) -> str:
        return self.construct[language.name].replace("{class}", cls).replace("{args}", ", ".join(args))

    def render(self, f: Field, value, language: Language) -> str:
        """A pinned value as code; `constant` fields come only from the table, never from the model."""
        if f.type == "int" and type(value) is int:
            return str(value)
        if f.type == "string" and isinstance(value, str):
            return string_literal(value, language)
        if f.type == "spec" and isinstance(value, str):
            return self.new(f.cls, [string_literal(value, language)], language)
        if f.type == "random_bytes" and type(value) is int and value > 0:
            return self.random_bytes[language.name].replace("{n}", str(value))
        raise Rejected("unknown_parameters")

    def default(self, f: Field, language: Language) -> str:
        if f.default is None:
            raise Rejected("missing_parameter")
        return f.default if f.type == "constant" else self.render(f, f.default, language)


def load(path: Path = TABLE) -> Table:
    doc = read_yaml(path)
    specs = []
    for s in doc["specs"]:
        fields = tuple(Field(a["field"], a["type"], a.get("default"), a.get("class")) for a in s["args"])
        if any(f.type not in TYPES for f in fields):
            raise ValueError(f"{path}: {s['class']}: unknown field type")
        specs.append(Spec(s["class"], fields))
    return Table(doc["position"], tuple(doc["encryptingModes"]), doc["construct"], doc["randomBytes"], tuple(specs))
