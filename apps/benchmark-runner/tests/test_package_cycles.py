import ast
import pathlib

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
# energy/ and analysis/ are search paths of their own; the runner appends energy/ to its path
OWN_ROOTS = (SCRIPTS / "energy", SCRIPTS / "analysis")


def root_of(path):
    return next((root for root in OWN_ROOTS if root in path.parents), SCRIPTS)


def search_path(path):
    root = root_of(path)
    if root == SCRIPTS:
        return (SCRIPTS, SCRIPTS / "energy")
    return (root, SCRIPTS) if root == SCRIPTS / "energy" else (root,)


def find(name, roots):
    for root in roots:
        if (root / f"{name}.py").is_file() or (root / name / "__init__.py").is_file():
            return root / name
    return next((root / name for root in roots if (root / name).is_dir()), None)


def resolve(node, path):
    if isinstance(node, ast.Import):
        return [find(a.name.split(".")[0], search_path(path)) for a in node.names]
    if node.level == 0:
        return [find(node.module.split(".")[0], search_path(path))]
    base = path.parents[node.level - 1]
    return [base / node.module.split(".")[0]] if node.module else [base / a.name for a in node.names]


def scripts_run(tree, path):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith(".py"):
            for root in search_path(path):
                if (root / node.value).is_file():
                    yield root / node.value
                    break


def targets(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield from (t for t in resolve(node, path) if t is not None)
    yield from scripts_run(tree, path)


def node_in(root, path):
    return path.relative_to(root).parts[0].removesuffix(".py")


def graph(root=SCRIPTS):
    """Each package and top-level module under root a node; a node's imports of itself are no edge."""
    files = [p for p in root.rglob("*.py") if "tests" not in p.relative_to(SCRIPTS).parts]
    edges = {node_in(root, p): set() for p in files}
    for path in files:
        for target in targets(path):
            if root in target.parents:
                edges[node_in(root, path)].add(node_in(root, target))
    return {node: (targets & set(edges)) - {node} for node, targets in edges.items()}


def reachable(edges, start):
    seen, todo = set(), list(edges[start])
    while todo:
        node = todo.pop()
        if node not in seen:
            seen.add(node)
            todo += edges[node]
    return seen


def cycles(edges):
    return [node for node in sorted(edges) if node in reachable(edges, node)]


def test_every_package_is_a_node_with_edges_into_energy_and_analysis():
    edges = graph()
    assert {"energy", "analysis", "stages", "session", "scope", "device", "results"} <= set(edges)
    assert "energy" in edges["energy_stage"] and "analysis" in edges["stages"]
    assert {"capture", "rails"} <= graph(SCRIPTS / "energy")["energy"] and "runner" in graph(SCRIPTS / "energy" / "sources")["manafa_source"]


def test_no_package_of_the_runner_imports_itself_through_another():
    found = {str(root.relative_to(SCRIPTS)): cycles(graph(root)) for root in (SCRIPTS, *OWN_ROOTS)}
    assert found == {".": [], "energy": [], "analysis": []}
