"""Named locations of one checkout, each derived once."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import roots

_ENGINE_OPERATIONS = "modules/preparation/src/main/resources/io/github/junekim0007/cryptobench/preparation/engine/engine-operations.yaml"
_APK = "modules/android/build/outputs/apk/release/android-release.apk"


@dataclass(frozen=True)
class Repo:
    root: Path

    algorithms = property(lambda self: self.root / roots.ALGORITHMS)
    config = property(lambda self: self.root / "config")
    default_global = property(lambda self: self.config / "global.yaml")
    default_results = property(lambda self: self.root / "results")
    runner = property(lambda self: self.root / roots.RUNNER)
    pipeline = property(lambda self: self.root / roots.PIPELINE)
    dependencies = property(lambda self: self.runner / "dependencies.py")
    energy = property(lambda self: self.runner / "energy")
    gradle_root = property(lambda self: self.root / "apps/benchmark")
    gradlew = property(lambda self: self.gradle_root / "gradlew")
    benchmark_cli = property(lambda self: self.gradle_root / "cli")
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
