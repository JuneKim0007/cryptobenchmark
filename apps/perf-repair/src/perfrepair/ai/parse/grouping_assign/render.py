"""One item's message: one YAML block of its family, the family's groups and the item, each with the facts code knows."""
from __future__ import annotations

import yaml

from ....catalog.groups import group_catalog
from ....catalog.interchange import KEY, interchange
from ....dto.grouping import KEY_APP_HELD, KEY_LABELS, Family, Item, Profile
from ....dto.grouping_state import Knowledge
from ....dto.signature import CONVENTION, UNKNOWN, Component, Signature

EXAMPLES = 3
NOT_KNOWN = "not known"
CATALOG, THIS_RUN = "catalog", "this run"


def _value(c: Component) -> str:
    return KEY_LABELS.get(c.value, c.value) if c.name == KEY else c.value


def _shown(c: Component) -> str:
    if c.status == UNKNOWN:
        return NOT_KNOWN
    return f"{_value(c)} (assumed)" if c.status == CONVENTION else _value(c)


def _placed(pairs: list[tuple[str, object]]) -> dict:
    """Each component under its contract; a contract with no fact is left out."""
    table = interchange()
    facts: dict[str, dict] = {}
    for name, value in sorted(pairs):
        facts.setdefault(table.contract_of(name), {})[name] = value
    return facts


def _item_facts(signature: Signature | None) -> dict:
    return _placed([(c.name, _shown(c)) for c in (signature.components if signature else ())])


def _group_facts(members: list[int], profiles: dict[int, Profile]) -> dict:
    """What any member knows: a join is checked against each member, so a value one member knows binds the group."""
    known: dict[str, set[str]] = {}
    for m in members:
        for c in (profiles[m].signature.components if profiles[m].signature else ()):
            if c.status != UNKNOWN and c.status != CONVENTION:
                known.setdefault(c.name, set()).add(_value(c))
    return _placed([(n, next(iter(v)) if len(v) == 1 else sorted(v)) for n, v in known.items()])


def _resolved(text: str | None) -> dict | None:
    """Each `name=value` of the trial's text, a number as a number; the whole text when a word has no value."""
    if not text:
        return None
    pairs = [t.split("=", 1) for t in text.split() if "=" in t]
    typed = {k: int(v) if v.isdigit() else v for k, v in pairs}
    return {**typed, "text": text} if len(pairs) != len(text.split()) else typed


def _group(gid: str, g, items: dict[int, Item], profiles: dict[int, Profile]) -> dict:
    row = {"id": gid, "source": CATALOG if group_catalog().variant_of(gid) else THIS_RUN, "description": g.description,
           "members": [f"{items[m].name} @ {items[m].provider}" for m in g.members[:EXAMPLES]]}
    if len(g.members) > EXAMPLES:
        row["moreMembers"] = len(g.members) - EXAMPLES
    facts = _group_facts(g.members, profiles)
    return {**row, "facts": facts} if facts else row


def render(item: Item, family: Family, knowledge: Knowledge, items: dict[int, Item], profiles: dict[int, Profile]) -> str:
    groups = knowledge.open_groups(family.id)
    shown = {"id": item.id, "type": item.type, "name": item.name, "provider": item.provider}
    resolved, facts = _resolved(item.resolved), _item_facts(profiles[item.id].signature)
    document = {"family": {"id": family.id, "description": family.description},
                "groups": [_group(gid, g, items, profiles) for gid, g in sorted(groups.items())],
                "item": {**shown, **({"resolved": resolved} if resolved else {}), **({"facts": facts} if facts else {})}}
    return yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=200).rstrip()
