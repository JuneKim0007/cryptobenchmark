"""Every perfrepair import points down the layer order in AGENTS.md; no package cycles; today's exceptions are the allowlists."""
import ast
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

ROOT = Path(__file__).parents[1] / "src" / "perfrepair"

LAYERS = [
    ("dto", "catalog"),
    ("files", "run_dir", "inputs", "log"),
    ("config",),
    ("data_handler",),
    ("result",),
    ("app", "scope", "screen", "source"),
    ("validation",),
    ("ai/runtime",),
    ("ai", "ai/evaluate", "ai/parse", "ai/review", "ai/suggest"),
    ("grouping", "repair", "command"),
    ("report",),
    ("guide", "check"),
    ("__main__",),
]
RANK = {layer: rank for rank, names in enumerate(LAYERS) for layer in names}

# (importer, imported) package pairs: reason; the #66 stage that removes it.
ALLOWLIST: dict[tuple[str, str], str] = {
    ("guide/steps", "app/__main__"): "guide calls the app command's main; no stage planned",
    ("guide/steps", "repair/__main__"): "guide calls the repair command's main; no stage planned",
}

# (importer, imported) package edges that close a cycle: reason; the #66 stage that removes it.
CYCLE_ALLOWLIST: dict[tuple[str, str], str] = {}


def _module(path: Path) -> list[str]:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    return parts[:-1] if parts[-1] == "__init__" else parts


def _layer(parts: list[str]) -> str:
    if parts and parts[-1] == "__main__":
        return "__main__"
    if parts[:1] == ["ai"] and len(parts) > 1:
        return "command" if parts[-1] == "command" else "/".join(parts[:2])
    return parts[0] if parts else "__main__"


def _package(parts: list[str]) -> str:
    depth = 3 if parts[:1] == ["ai"] else 2
    return "/".join(parts[:depth]) if len(parts) > 1 else parts[0]


def _targets(node: ast.AST, here: list[str], is_package: bool) -> list[list[str]]:
    if isinstance(node, ast.Import):
        return [a.name.split(".")[1:] for a in node.names if a.name.split(".")[0] == "perfrepair"]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level:
        base = here if is_package else here[:-1]
        base = base[:len(base) - node.level + 1] + (node.module.split(".") if node.module else [])
    elif (node.module or "").split(".")[0] == "perfrepair":
        base = node.module.split(".")[1:]
    else:
        return []
    out = []
    for a in node.names:
        sub = base + [a.name]
        out.append(sub if (ROOT.joinpath(*sub).is_dir() or ROOT.joinpath(*sub).with_suffix(".py").exists()) else base)
    return out


def _unit(parts: list[str]) -> str:
    if not parts or parts[-1] == "__main__":
        return "/".join(parts) or "__main__"
    return "/".join(parts[:2]) if parts[0] == "ai" and len(parts) > 2 else parts[0]


def _imports():
    for path in sorted(ROOT.rglob("*.py")):
        here = _module(path)
        for node in ast.walk(ast.parse(path.read_text())):
            for target in _targets(node, here, path.name == "__init__.py"):
                yield here, target


def _edges() -> set[tuple[str, str, str, str]]:
    return {(_layer(h), _layer(t), _package(h), _package(t)) for h, t in _imports()}


def _unit_edges() -> set[tuple[str, str]]:
    return {(_unit(h), _unit(t)) for h, t in _imports() if _unit(h) != _unit(t)}


def _cycle(edges: set[tuple[str, str]]) -> list[str]:
    graph: dict[str, set[str]] = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as e:
        return e.args[1]
    return []


def _violations() -> set[tuple[str, str]]:
    return {(a, b) for la, lb, a, b in _edges() if RANK[la] < RANK[lb]}


PRIVATE_PACKAGES = (["data_handler", "inbound", "probe"],)


def _private_reach(imports) -> list[tuple[str, str]]:
    return sorted({("/".join(h), "/".join(t)) for h, t in imports for p in PRIVATE_PACKAGES
                   if t[:len(p)] == p and len(t) > len(p) and t[len(p)].startswith("_") and h[:len(p)] != p})


def test_private_modules_are_imported_only_inside_their_package():
    assert _private_reach(_imports()) == []


def test_a_private_module_imported_from_outside_its_package_is_caught():
    assert _private_reach([(["app", "detect"], ["data_handler", "inbound", "probe", "_index"]),
                           (["data_handler", "inbound", "probe", "_probe"], ["data_handler", "inbound", "probe", "_index"])]) \
        == [("app/detect", "data_handler/inbound/probe/_index")]


def test_every_module_has_a_layer():
    assert {la for la, *_ in _edges()} | {lb for _, lb, *_ in _edges()} <= set(RANK)


def test_imports_follow_the_layer_order():
    assert sorted(_violations() - set(ALLOWLIST)) == []


def test_allowlist_has_no_stale_entries():
    assert sorted(set(ALLOWLIST) - _violations()) == []


def test_no_package_cycles():
    assert _cycle(_unit_edges() - set(CYCLE_ALLOWLIST)) == []


def test_cycle_allowlist_entries_each_break_a_cycle():
    edges = _unit_edges()
    assert sorted(e for e in CYCLE_ALLOWLIST if not _cycle(edges - (set(CYCLE_ALLOWLIST) - {e}))) == []
