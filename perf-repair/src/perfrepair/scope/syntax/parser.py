"""The one adapter over tree-sitter: source text → a neutral Node tree. Lazily imported: the parser is an optional extra."""
from __future__ import annotations

import importlib
from functools import cache

from ...source.language import JAVA, KOTLIN, Language
from .grammar import COMMENTS, kind_of
from .node import Node

_MODULES = {JAVA.name: "tree_sitter_java", KOTLIN.name: "tree_sitter_kotlin"}


class ParserMissing(Exception):
    """The `scope` extra is not installed; a caller records it, never falls back to another reading of the source."""


@cache
def _parser(language_name: str):
    try:
        runtime = importlib.import_module("tree_sitter")
        grammar = importlib.import_module(_MODULES[language_name])
    except ImportError as e:
        raise ParserMissing(str(e)) from e
    return runtime.Parser(runtime.Language(grammar.language()))


def available() -> bool:
    try:
        return all(_parser(name) is not None for name in _MODULES)
    except ParserMissing:
        return False


def parse(text: str, language: Language) -> Node:
    source = text.encode("utf8", "surrogateescape")
    tree = _parser(language.name).parse(source)
    return _neutral(tree.root_node, source)


def _neutral(root, source: bytes) -> Node:
    top = Node(root.type, kind_of(root.type), root.start_byte, root.end_byte, root.start_point[0] + 1,
               root.end_point[0] + 1, None, root.has_error, source)
    stack = [(root, top)]
    while stack:
        ts_node, node = stack.pop()
        for i, child in enumerate(ts_node.named_children):
            if child.type in COMMENTS:
                continue
            made = Node(child.type, kind_of(child.type), child.start_byte, child.end_byte, child.start_point[0] + 1,
                        child.end_point[0] + 1, node, child.has_error, source)
            node.children.append(made)
            name = ts_node.field_name_for_named_child(i)
            if name:
                node.fields.setdefault(name, made)
            stack.append((child, made))
    return top
