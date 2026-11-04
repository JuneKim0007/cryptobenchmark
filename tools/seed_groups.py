"""Proposes apps/perf-repair/src/perfrepair/catalog/groups.yaml rows from the signature over every catalogued name, for a
person to review before committing: never run by a pipeline. A name its signature leaves open is left to the model."""
import collections
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps/perf-repair/src"))

from perfrepair.catalog.families import Families  # noqa: E402
from perfrepair.catalog.groups import row_contracts  # noqa: E402
from perfrepair.catalog.interchange import INPUT, KEY, OUTPUT, interchange  # noqa: E402
from perfrepair.catalog.names import Names, fold  # noqa: E402
from perfrepair.dto.grouping import KEY_APP_HELD  # noqa: E402
from perfrepair.grouping.signature import signature  # noqa: E402

TYPES = ROOT / "apps/perf-repair/src/perfrepair/catalog/types.yaml"
SOURCE = "tools/seed_groups.py over catalog/algorithm-names.yaml and catalog/types.yaml, reviewed by a person"
PASSWORD_BASED, ID_LENGTH = "passwordBased", 38


def catalogued(families, names):
    """Family to names: types.yaml places a name; an engine type of one family, or a password-based name, places itself."""
    doc = yaml.safe_load(TYPES.read_text())
    placed = collections.defaultdict(set, {f: set(block["rows"]) for f, block in doc["families"].items()})
    rowed = {(families.by_id[f].type, fold(n)) for f, ns in placed.items() for n in ns}
    for engine_type in sorted(families.types):
        kinds = families.key_kinds(engine_type)
        for name in sorted(set(names.names.get(engine_type, {}).values())):
            if (engine_type, fold(name)) in rowed:
                continue
            read = signature(engine_type, name, None, KEY_APP_HELD, names).known()
            if len(kinds) == 1:
                placed[families.of(engine_type, kinds[0]).id].add(name)
            elif read.get(PASSWORD_BASED) == fold("true"):
                placed[families.of(engine_type, "unknown").id].add(name)
    return placed


def group_id(family, name):
    """A family's first letters first: one name can sit in two families, so its id cannot be the name alone."""
    slug = re.sub(r"[^a-z0-9.-]+", "-", name.lower()).strip("-")
    engine, kind = family.split(".")
    return f"{engine[:6]}-{kind[0]}-{slug}"[:ID_LENGTH].rstrip("-.")


def describe(engine_type, stands):
    facts = "; ".join(f"{c}: " + ", ".join(f"{k}={v}" for k, v in sorted(stands[c].items())) for c in (INPUT, OUTPUT) if stands[c])
    return f"Predefined {engine_type} group. {facts}."


def row(family, engine_type, group):
    stands = row_contracts([group[0][1]])
    return {"id": group_id(family, group[0][0]), "description": describe(engine_type, stands), "contracts": stands,
            "members": [{"type": engine_type, "name": n} for n, _ in group]}


def propose():
    families, names = Families.load(), Names.load()
    out, left = {}, []
    for family, rows in sorted(catalogued(families, names).items()):
        engine_type = families.by_id[family].type
        identical = collections.defaultdict(list)
        for name in sorted(rows, key=fold):
            sig = signature(engine_type, name, None, KEY_APP_HELD, names)
            if not sig.decided:
                left.append(f"{family} {name}")
                continue
            identical[tuple(i for i in sig.identity if interchange().contract_of(i[0]) != KEY)].append((name, sig))
        out[family] = [row(family, engine_type, group) for group in identical.values()]
    return {"schemaVersion": 1, "source": SOURCE, "families": out}, left


def main():
    document, left = propose()
    print(yaml.safe_dump(document, sort_keys=False, width=200), end="")
    for name in left:
        print(f"left to the model: {name}", file=sys.stderr)


if __name__ == "__main__":
    main()
