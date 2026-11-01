"""Parses one Java method or Kotlin function: name, parameters, return type, and the header rewritten as a public static member."""
import re
from dataclasses import dataclass

COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
# Only leading comments and annotations are dropped: a body's string literal may hold "//".
ANNOTATION = re.compile(r"@[\w.]+(\s*\([^()]*\))?")
JAVA_DROPPED = {"public", "protected", "private", "static", "final", "abstract", "synchronized", "strictfp", "default"}
KOTLIN_DROPPED = {"public", "protected", "private", "internal", "override", "open", "final", "inline", "tailrec", "external"}
# Signature.returns: None for void or Unit, INFERRED for an expression body without a declared type.
INFERRED = "?"
KOTLIN_UNSUPPORTED = {"suspend": "suspend_function", "operator": "operator_function", "infix": "infix_function"}


class SignatureError(Exception):
    """The function's shape is outside what a wrapper can call; the message is the not_compilable reason."""


@dataclass(frozen=True)
class Parameter:
    name: str
    type: str


@dataclass(frozen=True)
class Signature:
    name: str
    parameters: tuple
    returns: str | None
    member: str


def split_top(text, separator=","):
    parts, depth, current = [], 0, []
    for char in text:
        depth += char in "(<[{"
        depth -= char in ")>]}"
        if char == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    tail = "".join(current)
    return [p.strip() for p in parts + [tail] if p.strip()] if parts or tail.strip() else []


def closing(text, opened):
    depth = 0
    for index in range(opened, len(text)):
        depth += text[index] == "("
        depth -= text[index] == ")"
        if depth == 0:
            return index
    raise SignatureError("unparseable_signature: unbalanced parentheses")


def header(source):
    text = source.strip()
    while (leading := COMMENTS.match(text) or ANNOTATION.match(text)):
        text = text[leading.end():].strip()
    opened = text.find("(")
    brace = text.find("{")
    if opened < 0 or (0 <= brace < opened):
        raise SignatureError("not_a_function: no parameter list before the first brace")
    return text, opened, closing(text, opened)


def bare_type(text):
    return ANNOTATION.sub(" ", text).strip()


def java(source):
    text, opened, closed = header(source)
    prefix = ANNOTATION.sub(" ", text[:opened]).split()
    if not prefix or not re.match(r"^[A-Za-z_]\w*$", prefix[-1]):
        raise SignatureError("unparseable_signature: no method name")
    name, words = prefix[-1], [w for w in prefix[:-1] if w not in JAVA_DROPPED]
    if words and words[0].startswith("<"):
        raise SignatureError("generic_function: type parameters")
    if not words:
        raise SignatureError("unparseable_signature: no return type")
    returns = " ".join(words)
    parameters = []
    for raw in split_top(text[opened + 1:closed]):
        tokens = [t for t in bare_type(raw).split() if t != "final"]
        if len(tokens) < 2:
            raise SignatureError(f"unparseable_signature: parameter {raw}")
        if "..." in tokens[-2]:
            raise SignatureError(f"vararg_parameter: {raw}")
        parameters.append(Parameter(tokens[-1], " ".join(tokens[:-1])))
    rendered = ", ".join(f"{p.type} {p.name}" for p in parameters)
    member = f"public static {returns} {name}({rendered}){text[closed + 1:]}"
    return Signature(name, tuple(parameters), None if returns == "void" else returns, member)


def kotlin(source):
    text, opened, closed = header(source)
    prefix = ANNOTATION.sub(" ", text[:opened]).split()
    if "fun" not in prefix:
        raise SignatureError("not_a_function: no fun keyword")
    at = prefix.index("fun")
    for word in prefix[:at]:
        if word in KOTLIN_UNSUPPORTED:
            raise SignatureError(KOTLIN_UNSUPPORTED[word])
        if word not in KOTLIN_DROPPED:
            raise SignatureError(f"unparseable_signature: modifier {word}")
    rest = prefix[at + 1:]
    if rest and rest[0].startswith("<"):
        raise SignatureError("generic_function: type parameters")
    if len(rest) != 1 or not re.match(r"^[A-Za-z_]\w*$", rest[0]):
        raise SignatureError(f"extension_function: {' '.join(rest)}" if rest and "." in rest[-1] else "unparseable_signature: no function name")
    parameters = []
    for raw in split_top(text[opened + 1:closed]):
        declared = bare_type(raw)
        if declared.startswith("vararg "):
            raise SignatureError(f"vararg_parameter: {raw}")
        name, _, typed = declared.partition(":")
        if not typed:
            raise SignatureError(f"unparseable_signature: parameter {raw}")
        parameters.append(Parameter(name.strip(), split_top(typed, "=")[0].strip()))
    tail = text[closed + 1:]
    returns = None
    typed = re.match(r"\s*:\s*", tail)
    if typed:
        end = next((i for i, c in enumerate(tail) if c in "{=" and i > typed.end()), len(tail))
        returns = tail[typed.end():end].strip() or None
    elif re.match(r"\s*\{", tail):
        returns = "Unit"
    else:
        returns = INFERRED
    rendered = ", ".join(f"{p.name}: {p.type}" for p in parameters)
    member = f"fun {rest[0]}({rendered}){tail}"
    return Signature(rest[0], tuple(parameters), None if returns == "Unit" else returns, member)
