"""Every perfrepair import points down the layer order in AGENTS.md; today's exceptions are ALLOWLIST."""
import ast
from pathlib import Path

ROOT = Path(__file__).parents[1] / "src" / "perfrepair"

LAYERS = [
    ("dto", "catalog"),
    ("files", "run_dir"),
    ("data_handler",),
    ("result",),
    ("app", "scope"),
    ("validation",),
    ("ai/runtime", "env"),
    ("ai", "ai/evaluate", "ai/parse", "ai/review", "ai/suggest"),
    ("grouping", "repair", "command"),
    ("report",),
    ("guide", "check"),
    ("__main__",),
]
RANK = {layer: rank for rank, names in enumerate(LAYERS) for layer in names}

# (importer, imported) package pairs: reason; the #66 stage that removes it.
ALLOWLIST: dict[tuple[str, str], str] = {
    ("ai/review/grouping_review", "grouping/report"): "supervisor reads groups.json; B5 (S3) read_groups",
    ("validation/grouping", "grouping/catalog"): "gates read the family catalog; B6 (S4a) catalog/families.py",
    ("validation/parse", "grouping/catalog"): "assign gate reads the family catalog; B6 (S4a)",
    ("ai/parse/grouping_assign", "grouping/catalog"): "assign kind reads the family catalog; B6 (S4a)",
    ("ai/parse/grouping_assign", "grouping/paths"): "assign kind locates grouping files; B7 (S4b) run_dir",
    ("ai/review/grouping_review", "grouping/paths"): "supervisor locates grouping files; B7 (S4b) run_dir",
    ("ai/parse/grouping_assign", "grouping/state"): "assign kind projects cursor and knowledge; B8 (S5)",
    ("guide/steps", "app/__main__"): "guide calls the app command's main; no stage planned",
    ("guide/steps", "repair/__main__"): "guide calls the repair command's main; no stage planned",
}


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


def _edges() -> set[tuple[str, str, str, str]]:
    edges = set()
    for path in sorted(ROOT.rglob("*.py")):
        here = _module(path)
        for node in ast.walk(ast.parse(path.read_text())):
            for target in _targets(node, here, path.name == "__init__.py"):
                edges.add((_layer(here), _layer(target), _package(here), _package(target)))
    return edges


def _violations() -> set[tuple[str, str]]:
    return {(a, b) for la, lb, a, b in _edges() if RANK[la] < RANK[lb]}


def test_every_module_has_a_layer():
    assert {la for la, *_ in _edges()} | {lb for _, lb, *_ in _edges()} <= set(RANK)


def test_imports_follow_the_layer_order():
    assert sorted(_violations() - set(ALLOWLIST)) == []


def test_allowlist_has_no_stale_entries():
    assert sorted(set(ALLOWLIST) - _violations()) == []
