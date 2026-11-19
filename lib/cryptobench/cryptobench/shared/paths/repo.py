"""Named locations of one checkout, each derived once."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import roots
from .names import CONFIG_FOLDER, ENGINE_OPERATIONS, GLOBAL, SETUP_CATALOG

_KOTLIN_NAME_USERS = ("modules/environment/discovery/src/main/kotlin", "modules/config/src/main/kotlin", "modules/preparation/src/main/kotlin",
                      "modules/benchmark/src/main/kotlin", "modules/android/src/androidTest/kotlin", "cli/src/main/kotlin")
_APK = "modules/android/build/outputs/apk/release/android-release.apk"
# what builds the measuring code: the device app and test APK, the host's BenchKt, their dependency versions, the catalogues they read
_TIMED_CODE = (*(f"apps/benchmark/modules/{m}/src/main/**/*" for m in ("jca", "settings", "files", "document", "preparation", "benchmark")),
               "apps/benchmark/modules/android/src/**/*", "apps/benchmark/modules/android/build.gradle", "apps/benchmark/cli/src/main/**/*",
               "apps/benchmark/gradle/libs.versions.toml", f"{roots.ALGORITHMS}/{SETUP_CATALOG}", f"{roots.ALGORITHMS}/{ENGINE_OPERATIONS}")
# what launches, orders, retries, gates and reads energy around the timed code
_RUNNER_CODE = ("lib/cryptobench/cryptobench/stages/measurement/**/*.py", f"{roots.RUNNER}/energy/**/*.py", f"{roots.RUNNER}/energy/*.pbtx")


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
    energy_trace_config = property(lambda self: self.energy / "energy.pbtx")
    gradle_root = property(lambda self: self.root / "apps/benchmark")
    gradlew = property(lambda self: self.gradle_root / "gradlew")
    benchmark_cli = property(lambda self: self.gradle_root / "cli")
    kotlin_files_module = property(lambda self: self.gradle_root / "modules/files/src/main/kotlin")
    kotlin_name_users = property(lambda self: tuple(self.gradle_root / s for s in _KOTLIN_NAME_USERS))
    apk = property(lambda self: self.gradle_root / _APK)
    timed_code = property(lambda self: _TIMED_CODE)
    runner_code = property(lambda self: _RUNNER_CODE)
    engine_operations = property(lambda self: self.algorithms / ENGINE_OPERATIONS)
    setup_catalog = property(lambda self: self.algorithms / SETUP_CATALOG)
    perf_repair = property(lambda self: self.root / "apps/perf-repair")
    perf_repair_source = property(lambda self: self.perf_repair / "src")
    perfrepair_settings = property(lambda self: self.perf_repair / "perfrepair.yaml")
    dotenv = property(lambda self: self.perf_repair / ".env")
    library = property(lambda self: self.root / "lib/cryptobench")
    defaults = property(lambda self: self.root / "parity/defaults.yaml")


def repo(root: Path | str | None = None) -> Repo:
    return Repo(Path(root) if root is not None else roots.code_root())
