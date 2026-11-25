#!/usr/bin/env python3
"""Kotlin file names: the :files module equals Python's CONTRACT, and no file name is written by hand outside it.
Mirrored constants: each Python copy of a Kotlin value equals it."""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

from cryptobench.shared import paths

ROOT = paths.code_root()
MODULE = paths.repo().kotlin_files_module
SOURCES = paths.repo().kotlin_name_users
OWNER = re.compile(r"^object (\w+)", re.M)
CONSTANT = re.compile(r'^\s*const val (\w+) = "([^"]*)"', re.M)
LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')
HAND_BUILT = re.compile(r'\bFile\([^"]*,\s*"[\w.]')
PACKAGE = "io/github/junekim0007/cryptobench/"
# python module, name -> Kotlin (module, source set, file), pattern whose groups are the value
MIRRORS = (
    ("cryptobench.stages.measurement.session.case_isolation", "CASE_ARGUMENT", ("android", "androidTest", PACKAGE + "CaseFilter.kt"), r'(?m)^\s*const val ARGUMENT = "([^"]*)"'),
    ("cryptobench.stages.measurement.session.case_isolation", "REFUSED_PLAN", ("benchmark", "main", "RefusedPlanException.kt"), r'(?m)^\s*IllegalStateException\("(\w+:)'),
    ("cryptobench.stages.measurement.session.case_isolation", "LISTED", ("android", "androidTest", PACKAGE + "CryptoBenchmark.kt"), r"(?m)^\s*fun (measure)\(\)"),
    ("cryptobench.stages.measurement.benchmark", "DRY_CASE", ("android", "androidTest", PACKAGE + "EnergyDryBenchmark.kt"), r"(?m)^\s*fun (capture)\(\)"),
    ("cryptobench.stages.measurement.session.passes", "PASS_ARGUMENT", ("android", "androidTest", PACKAGE + "PassArguments.kt"), r'(?m)^\s*const val PASS = "([^"]*)"'),
    ("cryptobench.stages.measurement.session.passes", "SAMPLES_ARGUMENT", ("android", "androidTest", PACKAGE + "PassArguments.kt"), r'(?m)^\s*const val SAMPLES = "([^"]*)"'),
    ("cryptobench.stages.measurement.session.passes", "TIMING", ("config", "main", "global/dto/MeasurePass.kt"), r'(?m)^\s*const val TIMING = "([^"]*)"'),
    ("cryptobench.stages.measurement.session.passes", "ENERGY", ("config", "main", "global/dto/MeasurePass.kt"), r'(?m)^\s*const val ENERGY = "([^"]*)"'),
    ("cryptobench.stages.measurement.session.passes", "ALLOCATION", ("config", "main", "global/dto/MeasurePass.kt"), r'(?m)^\s*const val ALLOCATION = "([^"]*)"'),
    ("cryptobench.stages.discovery.probe", "HOST_MILLIS", ("android", "androidTest", PACKAGE + "DeviceProbe.kt"), r'(?m)^\s*const val HOST_MILLIS = "([^"]*)"'),
    *(("analysis.chart_input", group, ("preparation", "main", "prepare/ChartGroup.kt"), rf'(?m)^\s*{group}\((\d+), "([^"]*)"\)')
      for group in ("UNIDENTIFIED", "SYMMETRIC_CIPHER", "ASYMMETRIC_CIPHER", "SIGNATURE", "HASH", "MAC", "KEYGEN_SYMMETRIC", "KEYGEN_ASYMMETRIC")),
)
INSTRUMENTED = re.compile(r"test=(\w+)\\\[")


def kotlin_names(module: pathlib.Path) -> dict[str, str]:
    found = {}
    for path in sorted(module.rglob("*.kt")):
        text = path.read_text(encoding="utf-8")
        owner = OWNER.search(text)
        if owner:
            found |= {f"{owner.group(1)}.{name}": value for name, value in CONSTANT.findall(text)}
    return found


def disagreements(kotlin: dict[str, str], contract: dict[str, str]) -> list[str]:
    python = {constant: name for name, constant in contract.items()}
    problems = [f"kotlin only: {c} = {kotlin[c]}" for c in sorted(kotlin.keys() - python.keys())]
    problems += [f"python only: {c} = {python[c]}" for c in sorted(python.keys() - kotlin.keys())]
    return problems + [f"differs: {c}: kotlin {kotlin[c]}, python {python[c]}" for c in sorted(kotlin.keys() & python.keys()) if kotlin[c] != python[c]]


def _code_lines(path: pathlib.Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if not line.strip().startswith(("//", "/*", "*"))]


def literal_violations(repo: pathlib.Path, sources: tuple[pathlib.Path, ...], kotlin: dict[str, str]) -> set[str]:
    names = [value for constant, value in kotlin.items() if constant.startswith("FileNames.")]
    named = re.compile(r"(?<![\w.-])(?:" + "|".join(map(re.escape, names)) + r")(?![\w.-])")
    found = set()
    for source in sources:
        for path in sorted(source.rglob("*.kt")):
            relative = path.relative_to(repo).as_posix()
            for line in _code_lines(path):
                found |= {f"{relative}: names {hit}" for literal in LITERAL.findall(line) for hit in named.findall(literal)}
                if HAND_BUILT.search(line):
                    found.add(f"{relative}: builds a file from a literal: {line.strip()[:80]}")
    return found


def python_value(value) -> tuple[str, ...]:
    if isinstance(value, re.Pattern):
        found = INSTRUMENTED.search(value.pattern)
        return (found.group(1),) if found else (value.pattern,)
    return tuple(map(str, value)) if isinstance(value, tuple) else (str(value),)


def _module(name: str):
    if name.startswith("cryptobench.") or name in sys.modules:
        return importlib.import_module(name)
    spec = importlib.util.spec_from_file_location(name, paths.repo().runner.joinpath(*name.split(".")).with_suffix(".py"))
    module = sys.modules[name] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mirror_problems(kotlin_source=paths.repo().kotlin_source, mirrors=MIRRORS) -> list[str]:
    problems = []
    for module, name, kotlin, pattern in mirrors:
        python = python_value(getattr(_module(module), name))
        found = re.search(pattern, kotlin_source(*kotlin).read_text(encoding="utf-8"))
        if found is None:
            problems.append(f"mirror missing: {kotlin[2]} has no {pattern}")
        elif found.groups() != python:
            problems.append(f"mirror differs: {module}.{name} {python}, {kotlin[2]} {found.groups()}")
    return problems


def main() -> int:
    kotlin = kotlin_names(MODULE)
    problems = disagreements(kotlin, paths.CONTRACT | paths.CONTRACT_PARTS) + sorted(literal_violations(ROOT, SOURCES, kotlin))
    problems += mirror_problems()
    for line in problems:
        print(line)
    print("names: ok" if not problems else f"names: {len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
