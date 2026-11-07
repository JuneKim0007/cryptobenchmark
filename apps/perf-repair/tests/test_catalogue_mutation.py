"""The checks bite: a word no glossary holds or a dropped entry in a copy of the catalogues makes the load or catalogue_check fail; a changed measured value is no longer caught here."""
import copy
import random
import shutil
from functools import cache

import pytest
import yaml

from perfrepair.catalog.algorithms import DIRECTORY, SUFFIX, load
from perfrepair.catalog.families import Families
from perfrepair.catalog.groups import CATALOG as GROUPS, load as load_groups
from perfrepair.dto.coded import InputError
from perfrepair.validation.catalogue_entry import catalogue_check

LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)
SEEDS = range(10)


def _foreign_word(docs: dict, rng) -> str:
    family = rng.choice(sorted(docs))
    ident = rng.choice(sorted(docs[family]["algorithms"]))
    entry = docs[family]["algorithms"][ident]
    section = rng.choice(("required", "conditions", "lifecycle", "operations"))
    if section == "required" and entry["required"]:
        entry["required"][0]["name"] = "colour"
    elif section == "conditions":
        entry["conditions"]["colour"] = {"value": "red", "source": "inferred"}
    else:
        entry.setdefault("lifecycle", {})["reset"] = {"value": "sometimes", "source": "inferred"}
    return family, f"{ident}: a word no glossary holds in {section}"


def _dropped_entry(docs: dict, rng) -> str:
    family = rng.choice(sorted(docs))
    ident = rng.choice(sorted(docs[family]["algorithms"]))
    del docs[family]["algorithms"][ident]
    return family, f"{ident}: entry removed"


def _problems(target) -> list[str]:
    try:
        catalogue = load(target)
        groups = load_groups(GROUPS, catalogue=catalogue)
        return catalogue_check(catalogue, groups, Families.load())
    except InputError as e:
        return [str(e)]


@cache
def _originals() -> dict:
    return {p.name: yaml.load(p.read_text(), Loader=LOADER) for p in sorted(DIRECTORY.glob("*" + SUFFIX))}


@pytest.mark.parametrize("seed", SEEDS)
def test_one_random_change_fails_some_check(tmp_path, seed):
    rng = random.Random(seed)
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    docs = copy.deepcopy(_originals())
    name, what = rng.choice((_foreign_word, _dropped_entry))(docs, rng)
    (target / name).write_text(yaml.dump(docs[name], Dumper=DUMPER, sort_keys=False))
    assert _problems(target), what
