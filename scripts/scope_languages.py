"""One row per scope language: parser, source suffix, statement end, names it provides, the tag stub, the wrapper template."""
from dataclasses import dataclass

import scope_signature

# java.lang: both languages see these without an import.
JAVA_LANG = frozenset({"String", "System", "Math", "Integer", "Long", "Byte", "Short", "Character", "Boolean", "Object",
                       "StringBuilder", "Exception", "RuntimeException", "IllegalArgumentException", "IllegalStateException",
                       "Throwable", "Error", "Thread", "Number", "CharSequence", "UnsupportedOperationException"})
KOTLIN_DEFAULTS = frozenset({"ByteArray", "CharArray", "IntArray", "Charsets", "Unit", "Any", "Int", "Char", "require", "check",
                             "error", "requireNotNull", "checkNotNull", "println", "listOf", "mapOf", "setOf", "arrayOf",
                             "byteArrayOf", "lazy", "also", "apply", "let", "run", "with", "use", "toByteArray", "copyOf",
                             "copyOfRange", "plus", "repeat"})


@dataclass(frozen=True)
class Language:
    parse: object
    suffix: str
    statement_end: str
    provided: frozenset
    tag_stub: str
    wrapper: str


LANGUAGES = {
    "java": Language(
        parse=scope_signature.java, suffix=".java", statement_end=";", provided=JAVA_LANG,
        tag_stub='private static final String TAG = "scope";',
        wrapper="package {package};\n\n{imports}\n\npublic final class {name} {{\n\n    private {name}() {{\n    }}\n\n{stubs}{member}\n}}\n",
    ),
    "kotlin": Language(
        parse=scope_signature.kotlin, suffix=".kt", statement_end="", provided=JAVA_LANG | KOTLIN_DEFAULTS,
        tag_stub='private const val TAG = "scope"',
        wrapper="package {package}\n\n{imports}\n\nobject {name} {{\n\n{stubs}{member}\n}}\n",
    ),
}


def of(name):
    return LANGUAGES[name]
