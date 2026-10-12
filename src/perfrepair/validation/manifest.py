from __future__ import annotations

from pathlib import Path

from ..dto import BenchmarkManifest

COUNTED_BY = {"prepared": "prepared", "skipped": "skipped", "measured": "benchmark"}


def validate_manifest(manifest: BenchmarkManifest, base: Path) -> list[str]:
    problems = []
    for key, value in manifest.files.items():
        for rel in value if isinstance(value, list) else [value]:
            if not (Path(base) / rel).is_file():
                problems.append(f"files.{key}: {rel} does not exist")
    precedence = sorted(p.precedence for p in manifest.providers)
    if precedence != list(range(1, len(precedence) + 1)):
        problems.append(f"provider precedence {precedence} is not 1..{len(precedence)}")
    if len({p.name for p in manifest.providers}) != len(manifest.providers):
        problems.append("a provider is listed twice")
    for count, key in COUNTED_BY.items():
        if count in manifest.counts and key not in manifest.files:
            problems.append(f"counts.{count} given but files.{key} is absent")
    return problems
