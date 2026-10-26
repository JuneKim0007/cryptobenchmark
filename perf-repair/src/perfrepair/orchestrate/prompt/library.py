from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...dto.prompt import Charter, CorrectionPrompt, Lifetime, SystemPrompt
from ...files import read_yaml

PACKAGED = Path(__file__).resolve().parents[2] / "prompts"
REGISTRY = "prompts.yaml"
CORRECTION = "rejection"
SCHEMA_VERSION = 1


class PromptError(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    name: str
    file: str
    lifetime: Lifetime
    values: tuple[str, ...]


def read_registry(path: Path) -> dict[str, Entry]:
    doc = read_yaml(path)
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        raise PromptError(f"wrong_version: {path} schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
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
            for path in sorted(override.iterdir()):
                if path.name not in by_file:
                    raise PromptError(f"prompt_unknown: {path} matches no prompt in {REGISTRY} (known: {', '.join(sorted(by_file))})")
                sources[by_file[path.name]] = path
        absent = [str(p) for p in sources.values() if not p.is_file()]
        if absent:
            raise PromptError(f"prompt_missing: {', '.join(absent)}")
        return cls(entries, {name: path.read_text() for name, path in sources.items()}, sources)

    @classmethod
    def from_texts(cls, texts: dict[str, str]) -> "PromptLibrary":
        """The packaged prompts with the named ones replaced by text; for tests."""
        packaged = cls.load()
        unknown = sorted(set(texts) - set(packaged.entries))
        if unknown:
            raise PromptError(f"prompt_unknown: {', '.join(unknown)}")
        sources = {**packaged.sources, **{name: Path(f"<{name}>") for name in texts}}
        return cls(packaged.entries, {**packaged.texts, **texts}, sources)

    def system(self, name: str, **values) -> SystemPrompt:
        return SystemPrompt(name, self._fill(name, Lifetime.RUN, values))

    def correction(self, name: str, **values) -> CorrectionPrompt:
        return CorrectionPrompt(name, self._fill(name, Lifetime.TURN, values))

    def charter(self, name: str, schema: dict, **values) -> Charter:
        return Charter(self.system(name, **values), schema, self.texts[CORRECTION],
                       lambda problems: self.correction(CORRECTION, problems="\n".join(f"  - {p}" for p in problems)))

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
        text = self.texts[name]
        for key in entry.values:
            text = text.replace("{" + key + "}", str(values[key]))
        return text

