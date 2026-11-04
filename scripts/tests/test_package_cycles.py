import ast
import pathlib

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent


def node_of(path):
    return path.relative_to(SCRIPTS).parts[0].removesuffix(".py")


def targets(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            yield node.module.split(".")[0]


def graph():
    """Each package and top-level module of scripts/ a node; the package's own imports are no edge."""
    files = [p for p in SCRIPTS.rglob("*.py") if "tests" not in p.relative_to(SCRIPTS).parts]
    nodes = {node_of(p) for p in files}
    edges = {node: set() for node in nodes}
    for path in files:
        edges[node_of(path)] |= (set(targets(ast.parse(path.read_text()))) & nodes) - {node_of(path)}
    return edges


def reachable(edges, start):
    seen, todo = set(), list(edges[start])
    while todo:
        node = todo.pop()
        if node not in seen:
            seen.add(node)
            todo += edges[node]
    return seen


def test_no_package_of_scripts_imports_itself_through_another():
    edges = graph()
    assert [node for node in sorted(edges) if node in reachable(edges, node)] == []
