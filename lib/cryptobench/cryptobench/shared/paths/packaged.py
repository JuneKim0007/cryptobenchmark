"""Data files that ship inside a package: located through importlib, so an installed copy finds them too."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import NamedTuple


def packaged(package: str, name: str = "") -> Path:
    """The package's own folder when name is empty."""
    root = files(package)
    return Path(str(root.joinpath(name) if name else root)).resolve()


class PackagedFile(NamedTuple):
    package: str
    name: str = ""

    @property
    def path(self) -> Path:
        return packaged(self.package, self.name)


__all__ = ["packaged", "PackagedFile", "PERFREPAIR", "PROMPTS", "PROMPTS_REGISTRY", "SCREENING_CATALOG", "SDK_CONSTANTS", "UPGRADES_CATALOG", "BUNDLED_PROVIDERS", "KEY_CONTRACT",
           "LIBRARIES", "IGNORED_FILES", "EDIT_SPECS", "REPAIR_NAMES", "SETUP_CALLS", "RESULT_CRITERIA", "SCOPE_ENGINES", "SCOPE_PATTERNS", "SCOPE_RELATIONS", "ALL_PACKAGED"]
PERFREPAIR = PackagedFile("perfrepair")
PROMPTS = PackagedFile("perfrepair", "prompts")
PROMPTS_REGISTRY = PackagedFile("perfrepair", "prompts/prompts.yaml")
SCREENING_CATALOG = PackagedFile("perfrepair.catalog", "screening.yaml")
SDK_CONSTANTS = PackagedFile("perfrepair.catalog", "sdk-constants.yaml")
UPGRADES_CATALOG = PackagedFile("perfrepair.catalog", "upgrades.yaml")
BUNDLED_PROVIDERS = PackagedFile("perfrepair.catalog", "bundled-providers.yaml")
KEY_CONTRACT = PackagedFile("perfrepair.catalog", "key-contract.yaml")
LIBRARIES = PackagedFile("perfrepair.app.facts", "libraries.yaml")
IGNORED_FILES = PackagedFile("perfrepair.app.find", "ignored.yaml")
EDIT_SPECS = PackagedFile("perfrepair.repair.edit", "specs.yaml")
REPAIR_NAMES = PackagedFile("perfrepair.repair", "names.yaml")
SETUP_CALLS = PackagedFile("perfrepair.repair", "setup_calls.yaml")
RESULT_CRITERIA = PackagedFile("perfrepair.result", "criteria.yaml")
SCOPE_ENGINES = PackagedFile("perfrepair.scope", "engines.yaml")
SCOPE_PATTERNS = PackagedFile("perfrepair.scope", "patterns.yaml")
SCOPE_RELATIONS = PackagedFile("perfrepair.scope.units", "relations.yaml")
ALL_PACKAGED = (PROMPTS_REGISTRY, SCREENING_CATALOG, SDK_CONSTANTS, UPGRADES_CATALOG, BUNDLED_PROVIDERS, KEY_CONTRACT, LIBRARIES, IGNORED_FILES,
                EDIT_SPECS, REPAIR_NAMES, SETUP_CALLS, RESULT_CRITERIA, SCOPE_ENGINES, SCOPE_PATTERNS, SCOPE_RELATIONS)
