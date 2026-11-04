"""An item's signature: what its name, its trial's resolved and its key contract fix, known or unknown per component."""
from __future__ import annotations

from string import Template

from ..catalog.interchange import KEY_ASKED, KEY_NONE, Engine, Interchange, Rule, interchange
from ..catalog.names import Names, NamesError, fold
from ..dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, KEY_UNKNOWN
from ..dto.signature import CONVENTION, EXPORTABLE, KEY_MATERIAL, NON_EXPORTABLE, UNKNOWN, Component, Signature
from ..catalog.resolved import digest_name, function_parameters

NAME, KEY = "name", "key"
MATERIAL_OF_CONTRACT = {KEY_APP_HELD: EXPORTABLE, KEY_PROVIDER_HELD: NON_EXPORTABLE}


def _key(engine: Engine, contract: str) -> list[Component]:
    if engine.key == KEY_NONE:
        return []
    if contract != KEY_UNKNOWN:
        return [Component(KEY, contract)]
    return [Component(KEY, None, UNKNOWN) if engine.key == KEY_ASKED else Component(KEY, KEY_APP_HELD, CONVENTION)]


def _canonical(names: Names, engine_type: str, name: str) -> str | None:
    """None: no catalogued function for the name, or providers that mean two by it."""
    try:
        found = names.canonical(engine_type, name)
    except NamesError:
        return None
    return found.name if found.known else None


def _name_read(rule: Rule, groups: dict[str, str], engine: Engine, table: Interchange) -> dict[str, str]:
    values = {**engine.defaults, **{c: Template(v).substitute(groups) for c, v in rule.set.items()}}
    return {c: digest_name(v) if c in table.digest_components else fold(v) for c, v in values.items()}


def _components(rule: Rule, groups: dict[str, str], engine: Engine, resolved: str | None, table: Interchange) -> list[Component]:
    known = _name_read(rule, groups, engine, table)
    trial = dict(function_parameters(resolved))
    known.update({c: trial[c] for c in rule.resolved if c in trial})
    missing = {*rule.unknown, *(c for c in rule.resolved if c not in known)}
    return [Component(c, v) for c, v in known.items()] \
        + [Component(c, v, CONVENTION) for c, v in rule.convention.items()] \
        + [Component(c, None, UNKNOWN) for c in missing]


def _key_material(engine: Engine, recorded: str | None, contract: str) -> list[Component]:
    """Only an engine whose call makes a key has it: the trial's record, else what the key contract means, else unknown."""
    if KEY_MATERIAL not in engine.splits:
        return []
    value = recorded or MATERIAL_OF_CONTRACT.get(contract)
    return [Component(KEY_MATERIAL, value) if value else Component(KEY_MATERIAL, None, UNKNOWN)]


def signature(engine_type: str, name: str, resolved: str | None, contract: str, names: Names,
              table: Interchange | None = None, key_material: str | None = None) -> Signature:
    table = table or interchange()
    engine = table.engines.get(engine_type)
    if engine is None:
        return Signature((Component(NAME, None, UNKNOWN),))
    canonical = _canonical(names, engine_type, name)
    found = engine.rule_of(canonical) if canonical is not None else None
    parts = _components(*found, engine, resolved, table) if found else [Component(NAME, None, UNKNOWN)]
    parts += _key(engine, contract) + _key_material(engine, key_material, contract)
    return Signature(tuple(sorted(parts, key=lambda c: c.name)))
