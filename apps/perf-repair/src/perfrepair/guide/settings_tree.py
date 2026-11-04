"""A settings file and what it points at, through the parsers a run uses, read for `scripts/facade.py --check`; no model,
no device, no environment layer. Strict where a run only warns: a key nothing reads is a problem here."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..ai.runtime.prompt.library import PromptLibrary
from ..app.facts.target_set import listed_entries, resolve_targets
from ..config.load import Loaded, load
from ..config.settings import ConfigError, unknown_keys
from ..inputs.check import target_path, target_root
from ..inputs.table import FILE_CHAIN, ROWS, Row
from ..screen.catalog import load_catalog

PACKAGE = Path(__file__).resolve().parents[1]
TARGETS_KEY = "apps.targets"
SCREENING_KEY, PROMPTS_KEY = "device.screening.catalog", "paths.prompts"
# a key in the wrong file: the sections each other file owns
CRYPTO_SECTIONS = ("selection", "policy", "providers", "analysis", "run")
INDEX_SECTIONS = ("schemaVersion", "results", "crypto", "llm")
# each file-valued row and the parser a run gives it
PARSERS: dict[str, Callable[[Path], object]] = {SCREENING_KEY: load_catalog, PROMPTS_KEY: PromptLibrary.load}


@dataclass(frozen=True)
class Pointer:
    key: str
    path: Path
    kind: str


@dataclass
class LlmTree:
    pointers: list[Pointer] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def _misplaced(key: str, file: Path) -> str:
    section = key.split(".")[0]
    if section in CRYPTO_SECTIONS:
        return f"placement: {key} in {file} belongs in the global.yaml crypto.config names"
    if section in INDEX_SECTIONS:
        return f"placement: {key} in {file} belongs in the settings index"
    return f"unknown_key: {key} in {file}"


def _read_rows(loaded: Loaded, tree: LlmTree) -> None:
    for row in ROWS:
        if isinstance(row, Row) and row.chain == FILE_CHAIN:
            try:
                loaded.read(row)
            except ValueError as e:
                tree.problems.append(str(e))


def _file_pointers(loaded: Loaded, tree: LlmTree) -> None:
    for key, parser in PARSERS.items():
        value = loaded.settings.get(key)
        if not value:
            continue
        path = (loaded.file.parent / Path(str(value)).expanduser()).resolve()
        tree.pointers.append(Pointer(key, path, "overridden"))
        if path.exists():
            try:
                parser(path)
            except (ValueError, OSError, yaml.YAMLError) as e:
                tree.problems.append(f"invalid: {key} {path}: {e}")


def _targets(loaded: Loaded, tree: LlmTree) -> None:
    value = loaded.settings.get(TARGETS_KEY)
    if not value:
        tree.problems.append(f"no_targets: {TARGETS_KEY} is unset in {loaded.file}")
        return
    try:
        if isinstance(value, str):
            tree.pointers.append(Pointer(TARGETS_KEY, (loaded.file.parent / Path(value).expanduser()).resolve(), "targets"))
        entries, base = listed_entries(value, loaded.file)
        for i, entry in enumerate(entries):
            folder = (base / Path(target_root(entry) or target_path(entry)).expanduser()).resolve()
            tree.pointers.append(Pointer(f"{TARGETS_KEY}[{i}]", folder, "target"))
        found = resolve_targets(value, loaded.file)
    except (ValueError, yaml.YAMLError) as e:
        tree.problems.append(str(e))
        return
    if not found.apps:
        tree.problems.append(f"no_targets: {TARGETS_KEY} in {loaded.file}: {len(found.skipped)} candidates, none an app")


def llm_tree(file: Path) -> LlmTree:
    tree = LlmTree()
    try:
        loaded = load(file, {}, {})
    except ConfigError as e:
        tree.problems.append(str(e))
        return tree
    tree.problems += [_misplaced(key, file) for key in unknown_keys(loaded.settings.raw)]
    _read_rows(loaded, tree)
    _file_pointers(loaded, tree)
    _targets(loaded, tree)
    return tree


def packaged_catalogs() -> list[Path]:
    return sorted(PACKAGE.rglob("*.yaml"))
