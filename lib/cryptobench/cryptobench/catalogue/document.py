"""parse_yaml: a YAML text as the one shape its reader wants, or a coded refusal; DocumentKind: a versioned document's
accepted schemaVersion and the refusal its reader raises for another."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .coded import InputError

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


NAMED = "{name} schemaVersion {found} is not {version}"
AT_PATH = "{path}: schemaVersion {found} is not {version}"


@dataclass(frozen=True)
class DocumentKind:
    """message is each reader's own wording, kept until one shape is chosen (backlog R51)."""
    name: str
    version: int
    message: str = NAMED
    error: type[InputError] = InputError

    def accepts(self, found: object) -> bool:
        return found == self.version

    def check(self, doc: dict, path: Path | str | None = None) -> dict:
        found = doc.get("schemaVersion")
        if not self.accepts(found):
            raise self.error(self.message.format(name=self.name, found=found, version=self.version, path=path), path,
                             f"schemaVersion {found!r} is not {self.version}")
        return doc

    def read(self, path: Path | str, code: str = "invalid_yaml") -> dict:
        """The mapping at path through parse_yaml, refused with this kind's error on bad YAML or another schemaVersion."""
        return self.check(parse_yaml(Path(path).read_text(), str(path), code, error=self.error), path)
