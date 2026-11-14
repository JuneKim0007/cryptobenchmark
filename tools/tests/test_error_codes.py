"""The glossary (codes.yaml) both ways: every code Python raises or reports and every code a Kotlin main source writes is
in it; every code in it is written somewhere, or is a stored outcome."""
import ast
import pathlib
import re
import subprocess

from cryptobench.shared.errors.glossary import codes

REPO = pathlib.Path(__file__).resolve().parents[2]
PYTHON = ("apps/benchmark-runner", "apps/perf-repair/src", "apps/cli", "lib/cryptobench")
KOTLIN = "apps/benchmark"
HOLE = "\ue000"
# a text's leading word, `{...}` as a hole; it is a code when underscored, or one word before a colon
LEADING = re.compile(rf"^([a-z{HOLE}][a-z0-9_{HOLE}]*)([:; ]|$)")
REPORTERS = {"fail", "warn", "guarded", "terminate", "halt", "halt_of", "warning", "exit"}
PREFIXES = ("warning: ", "error: ", "skipped: ")
KOTLIN_LITERAL = re.compile(r'"((?:[^"\\$]|\\.|\$\{[^}]*\}|\$)*)"')
KOTLIN_TEMPLATE = re.compile(r"\$\{[^}]*\}|\$[A-Za-z_]\w*")
# a document kind, read as `unsupported_<kind>_schema`; never a code itself
KIND_ARGUMENT = re.compile(r"DocumentFile\.read\([^,]+,\s*$")


def tracked(root, pattern):
    """The files git lists under root, untracked ones included, so a new file counts before its commit."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", pattern],
                         cwd=REPO / root, capture_output=True, text=True, check=True).stdout
    return sorted(REPO / root / name for name in out.split("\0") if name)


def leading(text):
    """The code a text starts with as a pattern, a hole matching any word; None for prose."""
    found = LEADING.match(text)
    if not found:
        return None
    word, after = found.groups()
    if "_" in word.replace(HOLE, "") and not word.startswith("_") and not word.endswith("_"):
        return re.sub(f"{HOLE}+", "[a-z0-9_]+", word)
    return word if HOLE not in word and "_" not in word and after in (":", "") else None


def unprefixed(text):
    return next((text[len(p):] for p in PREFIXES if text.startswith(p)), text)


def literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else HOLE for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal(node.left)
    return None


def python():
    """(raised, written): codes a raise or reporter call starts its message with, and every string that starts with a code."""
    raised, written = {}, set()
    for root in PYTHON:
        for path in tracked(root, "*.py"):
            if "tests" in path.relative_to(REPO).parts or path.name.startswith("test_") or not path.is_file():
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if (text := literal(node)) is not None and (code := leading(unprefixed(text))):
                    written.add(code)
                call = node.exc if isinstance(node, ast.Raise) else node
                if not isinstance(call, ast.Call) or not call.args or (text := literal(call.args[0])) is None:
                    continue
                name = getattr(call.func, "id", getattr(call.func, "attr", ""))
                if name == "print" and text.startswith(PREFIXES):
                    text = unprefixed(text)
                elif not (isinstance(node, ast.Raise) or name in REPORTERS):
                    continue
                if code := leading(text):
                    raised.setdefault(code, []).append(f"{path.relative_to(REPO)}:{node.lineno}")
    return raised, written


def kotlin():
    """Every main-source string literal that starts with a code, after a warning:, error: or skipped: prefix."""
    found = {}
    for path in tracked(KOTLIN, "*.kt"):
        if "/src/main/" not in path.as_posix():
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            for m in KOTLIN_LITERAL.finditer(line):
                text = KOTLIN_TEMPLATE.sub(HOLE, m.group(1))
                if (code := leading(unprefixed(text))) and not KIND_ARGUMENT.search(line[:m.start()]):
                    found.setdefault(code, []).append(f"{path.relative_to(REPO)}:{n}")
    return found


def known(pattern):
    return any(re.fullmatch(pattern, code) for code in codes())


def test_every_raised_or_written_code_is_in_the_glossary():
    # a one-word code is left out: `families: ...` is prose as often as `invalid: ...` is a code
    raised = python()[0]
    for code, sites in kotlin().items():
        raised.setdefault(code, []).extend(sites)
    assert {p: sites for p, sites in raised.items() if "_" in p and not known(p)} == {}


def test_every_glossary_code_is_written_somewhere_or_is_a_stored_outcome():
    written = python()[1] | set(kotlin())
    unused = [c for c, e in codes().items() if e["kind"] != "outcome" and not any(re.fullmatch(p, c) for p in written)]
    assert unused == []
