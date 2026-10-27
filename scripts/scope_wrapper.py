"""Renders the generated androidTest sources: one wrapper per scope variant, and the GeneratedScopes catalog."""
from dataclasses import dataclass

import scope_inputs

PACKAGE = "io.github.junekim0007.cryptobench.scoped"
FOLDER = "modules/android/src/androidTest/java/io/github/junekim0007/cryptobench/scoped"
CATALOG = "GeneratedScopes"   # ScopeCatalog.GENERATED
WRAPPER = "ScopeFunction"
VARIANTS = ("before", "after")


@dataclass(frozen=True)
class Entry:
    scope: object
    signatures: dict
    stubs: tuple
    interop: object


def owner(scope_id, variant):
    return f"{PACKAGE}.s{scope_id}.{variant}.{WRAPPER}"


def import_line(line, language):
    text = line.strip().rstrip(";").strip()
    text = text if text.startswith("import ") else f"import {text}"
    return text + (";" if language == "java" else "")


def indent(text, by="    "):
    return "\n".join(by + line if line.strip() else "" for line in text.splitlines())


def wrapper(entry, variant):
    scope, signature = entry.scope, entry.signatures[variant]
    imports = "\n".join(import_line(line, scope.language) for line in scope.imports)
    stubs = "".join(f"    {stub}\n\n" for stub in entry.stubs)
    member = indent(signature.member.strip())
    folder = f"{FOLDER}/s{scope.id}/{variant}"
    if scope.language == "java":
        text = (f"package {PACKAGE}.s{scope.id}.{variant};\n\n{imports}\n\n"
                f"public final class {WRAPPER} {{\n\n    private {WRAPPER}() {{\n    }}\n\n{stubs}{member}\n}}\n")
        return f"{folder}/{WRAPPER}.java", text
    text = f"package {PACKAGE}.s{scope.id}.{variant}\n\n{imports}\n\nobject {WRAPPER} {{\n\n{stubs}{member}\n}}\n"
    return f"{folder}/{WRAPPER}.kt", text


def call(scope_id, variant, signature, arguments):
    return f"{owner(scope_id, variant)}.{signature.name}({', '.join(arguments)})"


def arguments(entry, prefix):
    names, lines = [], []
    for index, parameter in enumerate(entry.signatures["before"].parameters):
        names.append(f"{prefix}{index}")
        lines.append(f"val {prefix}{index} = {scope_inputs.expression(parameter, entry.scope)}")
    return names, lines


def round_trip(producer, consumer, produced, consumed):
    signature = consumer.signatures["before"]
    artifact = consumer.interop.index
    cast = scope_inputs.KOTLIN_TYPES[scope_inputs.kind(producer.signatures["before"].returns)]
    def consume(variant):
        values = [f"x as {cast}" if i == artifact else name for i, name in enumerate(consumed)]
        return f"{{ x -> {call(consumer.scope.id, variant, signature, values)} }}"
    produce = {v: f"{{ {call(producer.scope.id, v, producer.signatures['before'], produced)} }}" for v in VARIANTS}
    expected = produced[producer.interop.index]
    return (f"ScopeInterop.RoundTrip({expected}, {produce['before']}, {produce['after']}, "
            f"{consume('before')}, {consume('after')})")


def scope_function(entry, entries):
    plan = entry.interop
    if plan.check != "round_trip":
        names, lines = arguments(entry, "a")
        variants = {v: f"{{ {call(entry.scope.id, v, entry.signatures['before'], names)} }}" for v in VARIANTS}
        interop = "ScopeInterop.SameOutput" if plan.check == "same_output" else f"ScopeInterop.Unchecked({quoted(plan.reason)})"
    else:
        partner = entries[plan.partner]
        producer, consumer = (entry, partner) if plan.role == "produce" else (partner, entry)
        produced, produce_lines = arguments(producer, "p")
        consumed, consume_lines = arguments(consumer, "c")
        lines = produce_lines + consume_lines
        interop = round_trip(producer, consumer, produced, consumed)
        if entry is producer:
            names = produced
        else:
            lines.append(f"val artifact = lazy {{ {call(producer.scope.id, 'before', producer.signatures['before'], produced)} }}")
            names = [f"artifact.value as {scope_inputs.KOTLIN_TYPES[scope_inputs.kind(producer.signatures['before'].returns)]}"
                     if i == consumer.interop.index else name for i, name in enumerate(consumed)]
        variants = {v: f"{{ {call(entry.scope.id, v, entry.signatures['before'], names)} }}" for v in VARIANTS}
    body = "\n".join(lines + [f'return Scope("{entry.scope.id}", {variants["before"]}, {variants["after"]}, {interop})'])
    return f"    private fun s{entry.scope.id}(): Scope {{\n{indent(body, '        ')}\n    }}\n"


def quoted(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$") + '"'


def catalog(entries):
    """entries: {scope id: Entry}, in harness order."""
    listed = ", ".join(f"s{scope_id}()" for scope_id in entries)
    functions = "\n".join(scope_function(entry, entries) for entry in entries.values())
    return (f"package {PACKAGE}\n\n"
            "import io.github.junekim0007.cryptobench.Scope\n"
            "import io.github.junekim0007.cryptobench.ScopeCatalog\n"
            "import io.github.junekim0007.cryptobench.ScopeInputs\n"
            "import io.github.junekim0007.cryptobench.ScopeInterop\n\n"
            "@Suppress(\"UNUSED_VARIABLE\", \"USELESS_CAST\")\n"
            f"class {CATALOG} : ScopeCatalog {{\n\n"
            f"    override fun scopes(): List<Scope> = listOf({listed})\n\n{functions}}}\n")
