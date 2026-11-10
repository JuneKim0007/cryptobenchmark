"""Every code the runner stops, raises, warns or reports with, against runner-codes-frozen.txt: a code that changes shows as a diff."""
import ast, pathlib, re

RUNNER = pathlib.Path(__file__).resolve().parents[1]
FROZEN = pathlib.Path(__file__).with_name("runner-codes-frozen.txt")
CODED = re.compile(r"^([a-z][a-z0-9]*(?:_[a-z0-9*]+)+|[a-z*][a-z0-9*]*)(?::|$| )")
REPORTERS = ("fail", "warn", "guarded")


def literal(node):
    """A string argument's text with each `{...}` as `*`; a sum keeps its left side."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "*" for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal(node.left)
    return None


def reported(text):
    found = CODED.match(text)
    return found.group(1) if found else "uncoded: " + " ".join(text.split())[:60].rstrip()


def codes():
    found = set()
    for path in sorted(RUNNER.rglob("*.py")):
        if "tests" in path.relative_to(RUNNER).parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            call = node.exc if isinstance(node, ast.Raise) else node
            if not isinstance(call, ast.Call) or not call.args or (text := literal(call.args[0])) is None:
                continue
            name = getattr(call.func, "id", getattr(call.func, "attr", ""))
            if isinstance(node, ast.Raise) or name in REPORTERS:
                found.add(reported(text))
            elif name == "print" and text.startswith(("warning: ", "error: ")):
                found.add(reported(text.split(": ", 1)[1]))
    return found


def test_the_runners_codes_are_the_frozen_ones():
    frozen = {line for line in FROZEN.read_text().splitlines() if line}
    assert sorted(codes() - frozen) == [] and sorted(frozen - codes()) == []
