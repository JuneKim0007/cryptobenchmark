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
    ("device",),
    ("report", "review", "failure"),
    ("guide", "check"),
    ("__main__",),
]
RANK = {layer: rank for rank, names in enumerate(LAYERS) for layer in names}

# (importer, imported) package pairs: reason; the #66 stage that removes it.
ALLOWLIST: dict[tuple[str, str], str] = {
    ("guide/steps", "app/__main__"): "guide calls the app command's main; no stage planned",
    ("guide/steps", "repair/__main__"): "guide calls the repair command's main; no stage planned",
    ("guide/steps", "grouping/__main__"): "guide runs grouping assign and report for what coverage finds missing",
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


# (importer, what it must not import, exempt importers): finding sites reads no device data; only resolve meets it
DEVICE_LEVEL = (["data_handler"], ["grouping"], ["screen"], ["device"], ["run_dir"])
BOUNDARIES = (
    (["app", "find"], DEVICE_LEVEL + (["app", "facts"], ["app", "resolve"], ["app", "detect"]), ()),
    (["app"], (["data_handler"], ["grouping"], ["screen"], ["device"]), (["app", "resolve"],)),
    (["device"], (["app"],), ()),
)


def _crossings(imports) -> list[tuple[str, str]]:
    return sorted({("/".join(h), "/".join(t)) for h, t in imports for here, banned, exempt in BOUNDARIES
                   if h[:len(here)] == here and not any(h[:len(e)] == e for e in exempt)
                   and any(t[:len(b)] == b for b in banned)})


def test_app_and_device_keep_to_their_levels():
    assert _crossings(_imports()) == []


def test_a_crossing_is_caught():
    assert _crossings([(["app", "find", "scan"], ["data_handler", "inbound", "probe"]),
                       (["app", "detect"], ["data_handler", "inbound"]), (["app", "resolve"], ["data_handler", "inbound"]),
                       (["device", "stage"], ["app", "facts", "path_id"]), (["app", "facts", "gate"], ["app", "find", "sources"])]) \
        == [("app/detect", "data_handler/inbound"), ("app/find/scan", "data_handler/inbound/probe"),
            ("device/stage", "app/facts/path_id")]


# (attribute call, the modules allowed to make it): agents start one way, prompts load one way.
AGENT_ENTRY = {
    "start": ("ai/runtime/engine/ask", "ai/runtime/gateway/spawn"),
    "charter": ("kind", "ai/review/grouping_review/run", "ai/runtime/prompt/library", "ai/runtime/engine"),
}
BACKENDS = {"ClaudeConversations", "ClaudeCliConversations", "ClaudeClient"}


def _calls():
    for path in sorted(ROOT.rglob("*.py")):
        module = "/".join(_module(path))
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                target = getattr(getattr(node.func, "value", None), "id", "")
                yield module, name, target


def test_conversations_start_only_in_the_engine_and_charters_come_from_a_role():
    wrong = [(m, n) for m, n, t in _calls() if n == "start" and t in ("conversations", "self.conversations")
             and m not in AGENT_ENTRY["start"]]
    wrong += [(m, n) for m, n, t in _calls() if n == "charter" and t == "library"
              and not (m.endswith("/kind") or m in AGENT_ENTRY["charter"])]
    assert wrong == []


def test_a_real_backend_is_built_only_by_its_gateway():
    assert [(m, n) for m, n, _ in _calls() if n in BACKENDS and not m.startswith("ai/runtime/gateway/")] == []


def test_prompts_load_only_through_the_prompt_args():
    assert [m for m, n, t in _calls() if n == "load" and t == "PromptLibrary" and m != "ai/runtime/prompt/args"] == []


def test_scope_imports_no_model_repair_or_device_code():
    assert sorted({"/".join(t[:2]) for h, t in _imports() if h[:1] == ["scope"] and t[:1] in (["ai"], ["repair"], ["device"])}) == []
