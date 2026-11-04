"""The facade's check: every path exists, each file through its real parser, each key where it belongs, the direction rule."""
import pathlib
from dataclasses import dataclass, field

from perfrepair.catalog.screening import SCREENING
from perfrepair.guide.settings_tree import llm_tree, packaged_catalogs
from repo import BENCHMARK
from stages.config_check import ConfigCheckError, parse_all

from facade import tree as settings_tree
from facade.index import Index, SettingsIndexError, read_index
from facade.tree import CATALOG, CRYPTO, LLM, OVERRIDDEN, PACKAGED, ROOT_SIDE, Node

CRYPTO_CATALOGS = BENCHMARK / "modules/preparation/src/main/resources"
SCREENING_KEY = "device.screening.catalog"


@dataclass
class Checked:
    index: Index | None = None
    nodes: list = field(default_factory=list)
    problems: list = field(default_factory=list)


def _exists(node, problems):
    if not node.path.exists():
        problems.append(f"missing_file: {node.path} ({node.key} in {node.holder.path})")
        return False
    return True


def _results_parent(node, problems):
    # the root a run creates; only its parent must be there, so a mistyped folder is caught
    if not node.path.exists() and not node.path.parent.is_dir():
        problems.append(f"missing_file: {node.path.parent} (the folder of results in {node.holder.path})")


def _crypto(index, root, checked):
    held = [Node("crypto.config", index.crypto_config, "config", CRYPTO, root)]
    if index.harness_config:
        held.append(Node("crypto.harnessConfig", index.harness_config, "config", CRYPTO, root))
    present = [node for node in held if _exists(node, checked.problems)]
    checked.nodes += held
    if not present:
        return
    try:
        parsed = parse_all([node.path for node in present])
    except ConfigCheckError as e:
        checked.problems.append(f"config_invalid: {e}")
        return
    for node, one in zip(present, parsed):
        checked.nodes.append(Node("selection.testSet", pathlib.Path(one["testSet"]).resolve(), "config", CRYPTO, node))


def _llm(index, root, checked):
    node = Node("llm.config", index.llm_config, "config", LLM, root)
    checked.nodes.append(node)
    if not _exists(node, checked.problems):
        return None
    read = llm_tree(index.llm_config)
    checked.problems += read.problems
    for pointer in read.pointers:
        child = Node(pointer.key, pointer.path, pointer.kind, LLM, node)
        checked.nodes.append(child)
        _exists(child, checked.problems)
    return read


def _catalogs(read, checked):
    overrides = [p for p in read.pointers if p.kind == OVERRIDDEN] if read else []
    replaced = {SCREENING} if any(p.key == SCREENING_KEY for p in overrides) else set()
    packaged = [*packaged_catalogs(), *sorted(CRYPTO_CATALOGS.rglob("*.yaml"))]
    checked.nodes += [Node(str(p.name), p, CATALOG, CATALOG, None, PACKAGED) for p in packaged if p not in replaced]
    for pointer in overrides:
        files = [pointer.path] if pointer.path.is_file() else sorted(p for p in pointer.path.rglob("*") if p.is_file())
        checked.nodes += [Node(pointer.key, p, CATALOG, CATALOG, None, OVERRIDDEN) for p in files]


def check(settings):
    checked = Checked()
    try:
        index = checked.index = read_index(settings)
    except SettingsIndexError as e:
        checked.problems.append(str(e))
        return checked
    root = Node("settings", index.file, "index", ROOT_SIDE)
    results = Node("results", index.results, "results", ROOT_SIDE, root)
    _results_parent(results, checked.problems)
    checked.nodes += [root, results]
    _crypto(index, root, checked)
    read = _llm(index, root, checked)
    checked.problems += settings_tree.direction_problems(checked.nodes)
    _catalogs(read, checked)
    return checked
