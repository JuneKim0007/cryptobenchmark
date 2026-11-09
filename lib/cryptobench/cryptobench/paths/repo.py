"""Named locations of one checkout, each derived once."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import roots
from .names import CONFIG_FOLDER, ENGINE_OPERATIONS, GLOBAL

_ENGINE_OPERATIONS = "modules/preparation/src/main/resources/io/github/junekim0007/cryptobench/preparation/engine/" + ENGINE_OPERATIONS
_KOTLIN_NAME_USERS = ("modules/environment/discovery/src/main/kotlin", "modules/config/src/main/kotlin", "modules/preparation/src/main/kotlin",
                      "modules/benchmark/src/main/kotlin", "modules/android/src/androidTest/kotlin", "cli/src/main/kotlin")
_APK = "modules/android/build/outputs/apk/release/android-release.apk"


@dataclass(frozen=True)
class Repo:
    root: Path

    algorithms = property(lambda self: self.root / roots.ALGORITHMS)
    config = property(lambda self: self.root / CONFIG_FOLDER)
    default_global = property(lambda self: self.config / GLOBAL)
    default_results = property(lambda self: self.root / "results")
    runner = property(lambda self: self.root / roots.RUNNER)
    pipeline = property(lambda self: self.root / roots.PIPELINE)
    dependencies = property(lambda self: self.runner / "dependencies.py")
    energy = property(lambda self: self.runner / "energy")
    gradle_root = property(lambda self: self.root / "apps/benchmark")
    gradlew = property(lambda self: self.gradle_root / "gradlew")
    benchmark_cli = property(lambda self: self.gradle_root / "cli")
    kotlin_files_module = property(lambda self: self.gradle_root / "modules/files/src/main/kotlin")
    kotlin_name_users = property(lambda self: tuple(self.gradle_root / s for s in _KOTLIN_NAME_USERS))
    apk = property(lambda self: self.gradle_root / _APK)
    engine_operations = property(lambda self: self.gradle_root / _ENGINE_OPERATIONS)
    preparation_resources = property(lambda self: self.gradle_root / "modules/preparation/src/main/resources")
    perf_repair = property(lambda self: self.root / "apps/perf-repair")
    perf_repair_source = property(lambda self: self.perf_repair / "src")
    perfrepair_settings = property(lambda self: self.perf_repair / "perfrepair.yaml")
    dotenv = property(lambda self: self.perf_repair / ".env")
    library = property(lambda self: self.root / "lib/cryptobench")


def repo(root: Path | str | None = None) -> Repo:
    return Repo(Path(root) if root is not None else roots.code_root())
