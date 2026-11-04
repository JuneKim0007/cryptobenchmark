"""The functions no recorded run executed: python3 tools/unrun.py <coverage data file> <source folder>; one
`<file>:<line> <qualified name>` line each, candidates for dead code or a path no real run proves. Needs `coverage`."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import coverage


def _functions(tree: ast.AST, prefix: str = ""):
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = f"{prefix}{node.name}"
            if not isinstance(node, ast.ClassDef):
                yield name, node
            yield from _functions(node, name + ".")


def unrun(data_file: Path, source: Path) -> list[str]:
    data = coverage.CoverageData(basename=str(data_file))
    data.read()
    executed = {str(Path(f).resolve()): set(data.lines(f) or ()) for f in data.measured_files()}
    found = []
    for path in sorted(Path(source).rglob("*.py")):
        ran = executed.get(str(path.resolve()), set())
        for name, node in _functions(ast.parse(path.read_text())):
            # the def line runs at import; only a line of the body shows a call
            if not any(node.body[0].lineno <= n <= node.end_lineno for n in ran):
                found.append(f"{path.relative_to(source)}:{node.lineno} {name}")
    return found


if __name__ == "__main__":
    print("\n".join(unrun(Path(sys.argv[1]), Path(sys.argv[2]))))
