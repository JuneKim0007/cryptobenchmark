"""parse_yaml: a YAML text as the one shape its reader wants, or a coded refusal; DocumentKind: a versioned document's
accepted schemaVersion and the one refusal wording, Kotlin's, for another."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..errors.input_error import InputError

# the catalogues are about 1 MB: libyaml when the build has it, the pure-Python parser otherwise
SAFE_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _pure_mark(text: str) -> yaml.YAMLError | None:
    """libyaml marks the end of a text differently: the pure parser's events, never built into values, place the error."""
    try:
        for _ in yaml.parse(text, Loader=yaml.SafeLoader):
            pass
    except yaml.YAMLError as e:
        return e
    return None


def parse_yaml(text: str, where: str, code: str = "invalid_yaml", shape: type = dict, error: type[InputError] = InputError):
    """An empty text is an empty shape; YAML that does not parse, or parses to another shape, is `<code>: <where>: ...`."""
    try:
        doc = yaml.load(text, Loader=SAFE_LOADER)
    except yaml.YAMLError as e:
        e = _pure_mark(text) or e
        mark = getattr(e, "problem_mark", None)
        at = f" at line {mark.line + 1} column {mark.column + 1}" if mark else ""
        raise error(f"{code}: {where}: {getattr(e, 'problem', None) or 'not YAML'}{at}", where) from None
    if doc is None:
        return shape()
    if not isinstance(doc, shape):
        raise error(f"{code}: {where}: a {type(doc).__name__}, not a {'mapping' if shape is dict else shape.__name__}", where)
    return doc


def read_yaml(path: Path | str, shape: type = dict):
    """The file at path as parse_yaml reads it."""
    return parse_yaml(Path(path).read_text(), str(path), shape=shape)


@dataclass(frozen=True)
class DocumentKind:
    """name: the document in a refusal when no path is given; with a path, its file name, as Kotlin's SchemaVersion."""
    name: str
    version: int
    error: type[InputError] = InputError

    def accepts(self, found: object) -> bool:
        return _number(found) and found == self.version

    def check(self, doc: dict, path: Path | str | None = None) -> dict:
        found = doc.get("schemaVersion")
        name = Path(path).name if path is not None else self.name
        if not _number(found):
            raise self.error(f"missing_field: {name}: schemaVersion", path, "schemaVersion")
        if found != self.version:
            raise self.error(f"unsupported_schema_version: {name}: {found}, this build reads {self.version}", path,
                             f"{found}, this build reads {self.version}")
        return doc

    def read(self, path: Path | str, code: str = "invalid_yaml") -> dict:
        """The mapping at path through parse_yaml, refused with this kind's error on bad YAML or another schemaVersion."""
        return self.check(parse_yaml(Path(path).read_text(), str(path), code, error=self.error), path)


def _number(found: object) -> bool:
    # a YAML true is a Python int; Kotlin reads only a Number
    return isinstance(found, (int, float)) and not isinstance(found, bool)
