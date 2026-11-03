"""Links computed from lifecycles: a shared key, inverse operations of one engine type, a key's producer and its consumer."""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from ...dto.lifecycle import BOUNDED, PARTIALLY_BOUNDED, Requirement
from ...dto.site import Scope
from ...dto.unit import INVERSE, LINK_VIA, SHARED_KEY, Link
from .producers import consumer_links, key_requirements
from .relations import Relations, read_relations
from .shapes import Files

INPUT = "input"
KEY = "key"
PARAMETER = "parameter"


def linkable(s: Scope) -> bool:
    # an object never used or never read has nothing to keep in step with another
    return s.lifecycle is not None and s.lifecycle.status in (BOUNDED, PARTIALLY_BOUNDED)


def _named(s: Scope, name: str) -> list[Requirement]:
    return [r for r in s.lifecycle.requirements if r.name == name]


def _one_value(a: Scope, x: Requirement, b: Scope, y: Requirement, files: Files) -> bool:
    if x.origin != y.origin or x.line != y.line or x.origin not in LINK_VIA[SHARED_KEY]:
        return False
    # one line can declare several parameters: the two steps must not name different ones
    if x.origin != PARAMETER:
        return True
    taken_a, taken_b = files.parameters_taken(a, x), files.parameters_taken(b, y)
    return not taken_a or not taken_b or bool(set(taken_a) & set(taken_b))


def _same(a: Scope, b: Scope, name: str, files: Files) -> tuple[tuple[int, ...], tuple[int, ...], str] | None:
    """Two requirements with one origin and one line: the same value, read from the same place."""
    for x in _named(a, name):
        for y in _named(b, name):
            if _one_value(a, x, b, y, files):
                return (x.line, x.at), (y.line, y.at), x.origin
    return None


def _shared_key(a: Scope, b: Scope, files: Files) -> Link | None:
    found = _same(a, b, KEY, files)
    return Link(SHARED_KEY, a.id, b.id, found[0], found[1], found[2]) if found else None


def _direction(a: Scope, b: Scope, relations: Relations) -> tuple[Scope, Scope] | None:
    ops_a, ops_b = relations.operations(a), relations.operations(b)
    for produce, consume in relations.inverses.items():
        if produce in ops_a and consume in ops_b:
            return a, b
        if produce in ops_b and consume in ops_a:
            return b, a
    return None


def _key_lines(s: Scope) -> tuple[int, ...]:
    return tuple(sorted({n for r in key_requirements(s) for n in (r.line, r.at)}))


def _inverse_evidence(p: Scope, c: Scope, made_by: dict[str, set[str]], files: Files):
    for name in (KEY, INPUT):
        found = _same(p, c, name, files)
        if found:
            return found[0], found[1], name
    if made_by[p.id] & made_by[c.id]:
        return _key_lines(p), _key_lines(c), "producer"
    # both take their key from their caller, in one class: the same contract, though no caller is seen
    given = all(key_requirements(s) and all(r.origin == PARAMETER for r in key_requirements(s)) for s in (p, c))
    if given and files.shape(p).owner is not None and files.shape(p).owner == files.shape(c).owner:
        return _key_lines(p), _key_lines(c), PARAMETER
    return None


def _inverses(scopes: list[Scope], made_by: dict[str, set[str]], relations: Relations, files: Files) -> list[Link]:
    out = []
    for a, b in combinations(scopes, 2):
        ordered = _direction(a, b, relations) if a.engineType == b.engineType and a.algorithm == b.algorithm else None
        evidence = _inverse_evidence(*ordered, made_by, files) if ordered else None
        if evidence:
            out.append(Link(INVERSE, ordered[0].id, ordered[1].id, evidence[0], evidence[1], evidence[2]))
    return out


def _file_links(scopes: list[Scope], relations: Relations, files: Files) -> list[Link]:
    shared = [k for a, b in combinations(scopes, 2) if (k := _shared_key(a, b, files))]
    produced = consumer_links(scopes, relations, files)
    made_by: dict[str, set[str]] = defaultdict(set)
    for k in produced:
        made_by[k.b].add(k.a)
    return shared + produced + _inverses(scopes, made_by, relations, files)


def links_of(scopes: list[Scope], files: Files) -> list[Link]:
    by_file: dict[str, list[Scope]] = defaultdict(list)
    for s in sorted(filter(linkable, scopes), key=lambda s: (s.file, s.line, s.id)):
        by_file[s.file].append(s)
    relations = read_relations()
    return [k for file in sorted(by_file) if len(by_file[file]) > 1 for k in _file_links(by_file[file], relations, files)]
