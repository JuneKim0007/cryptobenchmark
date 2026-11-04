"""One row per scope language: parser, source suffix, statement end, names it provides, the tag stub, the wrapper template."""
from dataclasses import dataclass

from scope import signature as scope_signature

# java.lang of android.jar; both languages see these without an import. perf-repair's names.yaml holds the same set: test_scope_languages compares them.
JAVA_LANG = frozenset("""
AbstractMethodError Appendable ArithmeticException ArrayIndexOutOfBoundsException
ArrayStoreException AssertionError AutoCloseable Boolean BootstrapMethodError Byte
CharSequence Character Class ClassCastException ClassCircularityError ClassFormatError
ClassLoader ClassNotFoundException ClassValue CloneNotSupportedException Cloneable Comparable
Compiler Deprecated Double Enum EnumConstantNotPresentException Error Exception
ExceptionInInitializerError Float FunctionalInterface IllegalAccessError
IllegalAccessException IllegalArgumentException IllegalMonitorStateException
IllegalStateException IllegalThreadStateException IncompatibleClassChangeError
IndexOutOfBoundsException InheritableThreadLocal InstantiationError InstantiationException
Integer InternalError InterruptedException Iterable LinkageError Long MatchException Math
NegativeArraySizeException NoClassDefFoundError NoSuchFieldError NoSuchFieldException
NoSuchMethodError NoSuchMethodException NullPointerException Number NumberFormatException
Object OutOfMemoryError Override Package Process ProcessBuilder Readable Record
ReflectiveOperationException Runnable Runtime RuntimeException RuntimePermission SafeVarargs
SecurityException SecurityManager Short StackOverflowError StackTraceElement StackWalker
StrictMath String StringBuffer StringBuilder StringIndexOutOfBoundsException SuppressWarnings
System Thread ThreadDeath ThreadGroup ThreadLocal Throwable TypeNotPresentException
UnknownError UnsatisfiedLinkError UnsupportedClassVersionError UnsupportedOperationException
VerifyError VirtualMachineError Void
""".split())
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
