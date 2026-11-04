"""The resolved settings tree: its nodes, the direction rule over them, its printed lines and the document a run record keeps."""
import hashlib
from dataclasses import dataclass

CATALOG = "catalog"
PACKAGED, OVERRIDDEN = "packaged", "overridden"
ROOT_SIDE, CRYPTO, LLM = "root", "crypto", "llm"
DISPLAYED_DIGEST = 12


@dataclass(frozen=True)
class Node:
    """holder: the node whose file names this one, None at the root and for a packaged catalog, which nothing names."""
    key: str
    path: object
    kind: str
    side: str
    holder: object = None
    status: str = ""

    @property
    def digest(self):
        return hashlib.sha256(self.path.read_bytes()).hexdigest() if self.path.is_file() else None


def _ancestors(node):
    while node.holder is not None:
        node = node.holder
        yield node


def direction_problems(nodes):
    """A pointer back up its own chain, or at a file the other side holds; root -> side -> sub-file -> catalog only."""
    problems, held = [], {}
    pointers = [n for n in nodes if n.kind != "results" and n.status != PACKAGED]
    for node in pointers:
        above = next((a for a in _ancestors(node) if a.path == node.path), None)
        other = held.get(node.path)
        if above is not None:
            problems.append(f"direction: {node.key} in {node.holder.path} points up at {node.path}, the file {above.key} holds")
        elif other is not None and other.side != node.side:
            problems.append(f"direction: {node.key} in {node.holder.path} points sideways at {node.path}, "
                            f"{other.key} on the {other.side} side")
        held.setdefault(node.path, node)
    return problems


def _depth(node):
    return sum(1 for _ in _ancestors(node))


def _line(node):
    digest = node.digest
    mark = f"sha256:{digest[:DISPLAYED_DIGEST]}" if digest else "folder" if node.path.is_dir() else "to create"
    return f"{'  ' * (_depth(node) + 1)}{node.key}: {node.path}  {mark}" + (f"  {node.status}" if node.status else "")


def lines(nodes):
    tree = [n for n in nodes if n.kind != CATALOG]
    catalogs = [n for n in nodes if n.kind == CATALOG]
    shown = [f"tree: {tree[0].path}  sha256:{tree[0].digest[:DISPLAYED_DIGEST]}"]
    shown += [_line(n) for n in tree[1:]]
    shown += ["  catalogs:"] + [f"    {n.status}: {n.path}  sha256:{n.digest[:DISPLAYED_DIGEST]}" for n in catalogs]
    return shown


def document(nodes):
    return {"tree": [{"key": n.key, "path": str(n.path), "kind": n.kind, "side": n.side, "status": n.status, "sha256": n.digest,
                      "heldBy": str(n.holder.path) if n.holder else None} for n in nodes]}
