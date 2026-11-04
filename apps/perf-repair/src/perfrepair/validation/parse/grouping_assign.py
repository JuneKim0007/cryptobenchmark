from __future__ import annotations

import re

from ...catalog.groups import group_catalog
from ...dto.grouping import Item, Profile
from ...dto.grouping_state import Amendment, Answer, Group, Knowledge
from ...dto.signature import UNKNOWN
from ...catalog.families import Families
from ..json_reply import parse_object

SLUG = re.compile(r"^[a-z0-9][a-z0-9.-]{1,39}$")
MAX_DESCRIPTION = 400


def parse_answer(text: str) -> tuple[Answer | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    shape = []
    if not isinstance(d.get("group", ""), str):
        shape.append("group is not a string")
    new = d.get("newGroup") or {}
    if not isinstance(new, dict) or not all(isinstance(new.get(k) or "", str) for k in ("id", "description")):
        shape.append("newGroup is not an object of {id, description}")
    if not isinstance(d.get("amend") or [], list) or not all(
            isinstance(a, dict) and isinstance(a.get("group"), str) and isinstance(a.get("description"), str)
            for a in d.get("amend") or []):
        shape.append("amend is not a list of {group, description}")
    if not isinstance(d.get("reason", ""), str):
        shape.append("reason is not a string")
    if shape:
        return None, shape
    a = Answer.from_json(d)
    return Answer(a.group.strip(), a.newGroupId.strip(), a.newGroupDescription.strip(),
                  tuple(Amendment(x.group.strip(), x.description.strip()) for x in a.amend), a.reason.strip()), []


def description_problems(where: str, text: str) -> list[str]:
    if not text:
        return [f"{where}: description is empty"]
    if len(text) > MAX_DESCRIPTION:
        return [f"{where}: description is {len(text)} characters, more than {MAX_DESCRIPTION}"]
    return []


def _signature_problems(group: str, item: Item, family_groups: dict[str, Group], profiles: dict[int, Profile] | None) -> list[str]:
    """A join across a component both sides know; a member without a signature decides nothing."""
    profiles = profiles or {}
    mine = profiles[item.id].signature if item.id in profiles else None
    if mine is None or group not in family_groups:
        return []
    problems = []
    for member in family_groups[group].members:
        theirs = profiles[member].signature if member in profiles else None
        problems += [f"group {group!r}: member {member} has {name}={theirs.known().get(name, UNKNOWN)}, this item has "
                     f"{name}={mine.known().get(name, UNKNOWN)}; create another group"
                     for name in (mine.differing(theirs) if theirs else [])]
    return problems


def _isolation_problems(group: str, item: Item, family_groups: dict[str, Group], profiles: dict[int, Profile]) -> list[str]:
    """A generator of unknown key contract joins no group, and no item joins one holding it."""
    if not group or group not in family_groups:
        return []
    alone = [m for m in (item.id, *family_groups[group].members) if m in profiles and profiles[m].isolated]
    return [f"group {group!r}: item {m} joins no group: whether its generated key leaves the provider is unknown; "
            "create another group" for m in alone]


def _not_in_family(group: str, item: Item, knowledge: Knowledge, family_groups: dict[str, Group]) -> str:
    other = knowledge.groups[group].family if group in knowledge.groups else None
    fact = f"; it is of family {other}, never compared with this item's" if other and other != item.family else ""
    return f"group {group!r} is not a group of family {item.family}{fact} (its groups: {sorted(family_groups) or 'none yet'})"


def validate_answer(a: Answer, item: Item, knowledge: Knowledge, families: Families,
                    profiles: dict[int, Profile] | None = None) -> list[str]:
    problems = []
    if bool(a.group) == bool(a.newGroupId):
        problems.append("give exactly one of group (join) or newGroup.id (create)")
    family_groups = knowledge.open_groups(item.family)
    if a.group and a.group not in family_groups:
        problems.append(_not_in_family(a.group, item, knowledge, family_groups))
    problems += _signature_problems(a.group, item, family_groups, profiles)
    problems += _isolation_problems(a.group, item, family_groups, profiles or {})
    if a.newGroupId:
        if not SLUG.match(a.newGroupId):
            problems.append(f"newGroup.id {a.newGroupId!r} must match {SLUG.pattern}")
        if knowledge.taken(a.newGroupId):
            problems.append(f"newGroup.id {a.newGroupId!r} already exists; join it or choose another id")
        if a.newGroupId in families.by_id:
            problems.append(f"newGroup.id {a.newGroupId!r} is a family id")
        problems += description_problems("newGroup", a.newGroupDescription)
    targets = [x.group for x in a.amend]
    if len(set(targets)) != len(targets):
        problems.append("amend names a group twice")
    for x in a.amend:
        if x.group not in family_groups:
            problems.append(f"amend {x.group!r}: not a group of family {item.family}")
        if group_catalog().variant_of(x.group) is not None:
            problems.append(f"amend {x.group!r}: a catalog group's description is fixed")
        problems += description_problems(f"amend {x.group!r}", x.description)
    if not a.reason:
        problems.append("reason is empty")
    if knowledge.group_of(item.id) or item.id in knowledge.dropped:
        problems.append(f"item {item.id} is already decided")
    return problems
