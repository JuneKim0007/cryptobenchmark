"""Sorts a scope's dependencies into imported, language-provided, stubbed, left to the compiler, or unsatisfied."""
from dataclasses import dataclass

# Names both languages see without an import (java.lang); Kotlin adds its default-imported stdlib.
LANGUAGE = {"String", "System", "Math", "Integer", "Long", "Byte", "Short", "Character", "Boolean", "Object",
            "StringBuilder", "Exception", "RuntimeException", "IllegalArgumentException", "IllegalStateException",
            "Throwable", "Error", "Thread", "Number", "CharSequence", "UnsupportedOperationException"}
KOTLIN = {"ByteArray", "CharArray", "IntArray", "Charsets", "Unit", "Any", "Int", "Char", "require", "check", "error",
          "requireNotNull", "checkNotNull", "println", "listOf", "mapOf", "setOf", "arrayOf", "byteArrayOf", "lazy",
          "also", "apply", "let", "run", "with", "use", "toByteArray", "copyOf", "copyOfRange", "plus", "repeat"}
# The one stub shape: a log tag constant; anything else is never faked.
STUBS = {"TAG": {"java": 'private static final String TAG = "scope";', "kotlin": 'private const val TAG = "scope"'}}


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
    provided = LANGUAGE | (KOTLIN if language == "kotlin" else set())
    stubs, unsatisfied, deferred = [], [], []
    for name in dependencies:
        if name in names or name in provided:
            continue
        if name in STUBS:
            stubs.append(STUBS[name][language])
        elif wildcard:
            deferred.append(name)
        else:
            unsatisfied.append(name)
    return Resolution(tuple(stubs), tuple(unsatisfied), tuple(deferred))
