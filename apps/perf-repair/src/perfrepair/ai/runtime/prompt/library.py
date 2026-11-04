from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ....dto.document import DocumentKind
from ....dto.prompt import Charter, CorrectionPrompt, Lifetime, SystemPrompt, fill
from ....stop.halt import Coded
from ....files import read_yaml

PACKAGED = Path(__file__).resolve().parents[3] / "prompts"
REGISTRY = "prompts.yaml"
CORRECTION = "shared/rejection"
SCHEMA_VERSION = 1


class PromptError(Coded):
    pass


REGISTRY_DOC = DocumentKind("prompts", SCHEMA_VERSION, "wrong_version: {path} schemaVersion {found} is not {version}", PromptError)


@dataclass(frozen=True)
class Entry:
    name: str
    file: str
    lifetime: Lifetime
    values: tuple[str, ...]


def read_registry(path: Path) -> dict[str, Entry]:
    doc = read_yaml(path)
    REGISTRY_DOC.check(doc, path)
    return {name: Entry(name, e["file"], Lifetime(e["lifetime"]), tuple(e.get("values") or ()))
            for name, e in (doc.get("prompts") or {}).items()}


class PromptLibrary:
    """The only reader of prompt files: every prompt is read and checked once, at load."""

    def __init__(self, entries: dict[str, Entry], texts: dict[str, str], sources: dict[str, Path]):
        for name, entry in entries.items():
            missing = [v for v in entry.values if "{" + v + "}" not in texts[name]]
            if missing:
                raise PromptError(f"placeholder_missing: {sources[name]} lacks {', '.join('{' + v + '}' for v in missing)}")
        self.entries, self.texts, self.sources = entries, texts, sources

    @classmethod
    def load(cls, override: Path | None = None) -> "PromptLibrary":
        entries = read_registry(PACKAGED / REGISTRY)
        by_file = {e.file: e.name for e in entries.values()}
        sources = {name: PACKAGED / e.file for name, e in entries.items()}
        if override is not None:
            override = Path(override)
            if not override.is_dir():
                raise PromptError(f"missing_directory: {override} (--prompts)")
            for path in sorted(p for p in override.rglob("*") if p.is_file()):
                relative = path.relative_to(override).as_posix()
                if relative not in by_file:
                    raise PromptError(f"prompt_unknown: {path} matches no prompt in {REGISTRY} (known: {', '.join(sorted(by_file))})")
                sources[by_file[relative]] = path
        absent = [str(p) for p in sources.values() if not p.is_file()]
        if absent:
            raise PromptError(f"prompt_missing: {', '.join(absent)}")
        return cls(entries, {name: path.read_text() for name, path in sources.items()}, sources)

    def system(self, name: str, **values) -> SystemPrompt:
        return SystemPrompt(name, self._fill(name, Lifetime.RUN, values))

    def charter(self, name: str, schema: dict, inputs: str = "", **values) -> Charter:
        entry = self.entries[CORRECTION]
        if entry.lifetime is not Lifetime.TURN or entry.values != ("problems",):
            raise PromptError(f"value_mismatch: {CORRECTION} must be a turn prompt declaring only [problems]")
        return Charter(self.system(name, **values), schema, CorrectionPrompt(CORRECTION, self.texts[CORRECTION]), inputs,
                       tuple((n, self.origin(n)) for n in (name, CORRECTION)))

    def origin(self, name: str) -> str:
        """`packaged`, or the override file the prompt was read from."""
        path = self.sources[name]
        return "packaged" if path == PACKAGED / self.entries[name].file else str(path)

    def provenance(self, charter: Charter) -> dict[str, str]:
        return {name: str(self.sources[name]) for name in charter.prompts}

    def source(self, name: str) -> Path:
        return self.sources[name]

    def _fill(self, name: str, lifetime: Lifetime, values: dict) -> str:
        entry = self.entries.get(name)
        if entry is None:
            raise PromptError(f"prompt_unknown: {name} (known: {', '.join(sorted(self.entries))})")
        if entry.lifetime is not lifetime:
            raise PromptError(f"lifetime_mismatch: {name} lives for a {entry.lifetime.value}, asked as a {lifetime.value}")
        missing, unexpected = sorted(set(entry.values) - set(values)), sorted(set(values) - set(entry.values))
        if missing or unexpected:
            raise PromptError(f"value_mismatch: {name} missing {missing}, unexpected {unexpected}")
        return fill(self.texts[name], {key: values[key] for key in entry.values})

