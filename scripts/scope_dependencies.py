"""Sorts a scope's dependencies into imported, language-provided, stubbed, left to the compiler, or unsatisfied."""
from dataclasses import dataclass

import scope_languages

# The one stub shape: a log tag constant; anything else is never faked.
STUBBED = "TAG"


@dataclass(frozen=True)
class Resolution:
    stubs: tuple
    unsatisfied: tuple
    deferred: tuple


def imported(line):
    text = line.strip().removeprefix("import").strip().rstrip(";").strip()
    text = text.removeprefix("static ").strip()
    if " as " in text:
        return text.split(" as ")[-1].strip()
    return text.split(".")[-1]


def resolve(dependencies, imports, language):
    names = {imported(line) for line in imports}
    wildcard = "*" in names
    row = scope_languages.of(language)
    stubs, unsatisfied, deferred = [], [], []
    for name in dependencies:
        if name in names or name in row.provided:
            continue
        if name == STUBBED:
            stubs.append(row.tag_stub)
        elif wildcard:
            deferred.append(name)
        else:
            unsatisfied.append(name)
    return Resolution(tuple(stubs), tuple(unsatisfied), tuple(deferred))
