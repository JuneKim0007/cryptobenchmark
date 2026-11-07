"""The glossary closes over the catalogues and recipes.yaml: every word in them is defined, each spelled one way; every term is used or justified."""
from collections import defaultdict

import pytest
import yaml

from perfrepair.catalog.algorithms import COMMON, DIRECTORY, SUFFIX
from perfrepair.catalog.families import Families
from perfrepair.catalog.glossary import (ALL, DERIVED, GlossaryError, _override, deviation_problems, MEANS, UNUSED, VALUES, entry_terms, provider_key_problems, recipe_problems,
                                        recipe_terms, role_problems, roles, term_problems, tree, what_is)
from perfrepair.catalog.recipes import CATALOG as RECIPES
from perfrepair.catalog.groups import CATALOG as GROUPS
from perfrepair.catalog.names import CATALOG as NAMES_FILE, Names, NamesError, fold
from perfrepair.catalog.deviations import CATALOG as DEVIATIONS
from perfrepair.catalog.provider_builds import CATALOG as PROVIDER_BUILDS, ProviderBuildError, load as load_builds


def _catalogues():
    return {p.name[:-len(SUFFIX)]: yaml.safe_load(p.read_text()) for p in sorted(DIRECTORY.glob("*" + SUFFIX))}


def _terms():
    """Every term of the tree as (path, node)."""
    out = []
    def walk(node, path):
        if isinstance(node, dict) and MEANS in node:
            out.append((path, node))
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, dict) and k not in (VALUES, UNUSED):
                    walk(v, f"{path}.{k}" if path else str(k))
    walk({k: v for k, v in tree().items() if k != "schemaVersion"}, "")
    return out


def test_one_definition_a_subtree_and_a_section():
    assert what_is("algorithm.required.name", "peerPublicKey").startswith("The other party's public key")
    assert set(what_is("algorithm.required")) >= {"name", "passedTo", "recipe", "bytes", "sameGroupAs"}
    assert set(what_is("group")) >= {"family", "description", "exemplars", "algorithms", "members", "unidentified"}
    assert what_is("algorithm.conditions.authenticated.value", True).startswith("Decrypt or verify fails")


@pytest.mark.parametrize("path,value,names", [
    ("algorithm.nope", ALL, "valid here"), ("algorithm.required.name", "nope", "peerPublicKey"),
    ("algorithm.required", "x", "is a section"), ("algorithm.sourcedOnly.url", "x", "no term"),
    ("algorithm.conditions.output.bytes", "x", "no number")])
def test_an_unknown_key_or_value_is_coded_and_names_what_is_valid(path, value, names):
    with pytest.raises(GlossaryError, match=f"glossary_unknown: .*{names}"):
        what_is(path, value)


def test_every_key_and_value_of_every_catalogue_is_in_the_glossary():
    found = sorted({p for doc in _catalogues().values() for raw in doc["algorithms"].values() for p in term_problems(raw) + provider_key_problems(raw)})
    assert found == []


def test_each_key_path_spells_each_value_one_way():
    seen = defaultdict(lambda: defaultdict(set))
    for doc in _catalogues().values():
        for raw in doc["algorithms"].values():
            for path, value in entry_terms(raw):
                if isinstance(value, str):
                    seen[path][fold(value)].add(value)
    assert {(p, tuple(sorted(s))) for p, v in seen.items() for s in v.values() if len(s) > 1} == set()


def test_no_stored_value_says_a_fact_is_unsourced_or_a_required_row_says_none():
    for doc in _catalogues().values():
        for ident, raw in doc["algorithms"].items():
            assert "unsourced" not in str(raw), ident
            assert not [r for r in raw["required"] if r.get("value") == "none"], ident


def _recipes() -> dict:
    return yaml.safe_load(RECIPES.read_text())


def test_every_key_and_value_of_recipes_yaml_is_in_the_glossary_and_every_role_says_how_it_is_made():
    assert recipe_problems(_recipes()) == []
    assert role_problems() == []


def test_every_word_of_deviations_yaml_is_in_the_glossary():
    assert deviation_problems(yaml.safe_load(DEVIATIONS.read_text())) == []


def test_a_derived_term_is_refused_when_stored():
    raw = {"lifecycle": {"reinit": {"value": "perUse", "source": "inferred"}}}
    assert any("derived" in p for p in term_problems(raw))


def test_every_term_and_closed_value_is_used_or_justified():
    used = defaultdict(set)
    for doc in _catalogues().values():
        for raw in doc["algorithms"].values():
            for path, value in entry_terms(raw):
                used[path].update(value if isinstance(value, list) else [value])
    for path, value in recipe_terms(_recipes()):
        used[path].add(value)
    for path, values in _group_words().items():
        used[path].update(values)
    named = used["algorithm.required.name"] | used["algorithm.optional.name"] | used["recipe.args.role"]
    for name, role in roles().items():
        used[f"algorithm.role.{name}"].add(None) if name in named else None
        used["algorithm.make"].add(role["make"])
        used["algorithm.lives"].update(role["lives"].values() if isinstance(role["lives"], dict) else [role["lives"]])
    builds, names = yaml.safe_load(PROVIDER_BUILDS.read_text()), yaml.safe_load(NAMES_FILE.read_text())
    used.update({f"build.{k}": {None} for k in [*builds, "name", "selfReported", "providers.behaviour", "providers.registers", "providers.registers.builds", "providers.registers.names"]})
    held = [row["behaviour"] for row in builds["providers"].values()]
    deviations = yaml.safe_load(DEVIATIONS.read_text())
    used.update({f"deviation.{k}": {None} for k in [*deviations, "id", "fact", "builds", "names", "set"]})
    held += [row["set"] for row in deviations["deviations"].values()]
    for path, value in (pair for one in held for at, v in one.items() for pair in _override(at, v)):
        used[path].update(value if isinstance(value, list) else [value])
    used["build.origin"].update(row["origin"] for row in builds["builds"].values())
    used.update({f"names.{k}": {None} for k in names})
    used["names.engine"].update(names["names"])
    used.update({f"names.sized.{k}": {None} for k in ("name", "keySize")})
    used.update({f"names.transformations.{k}": {None} for k in names["transformations"]["Cipher"]})
    used["algorithm.direction"].update(tree()["algorithm"]["operations"]["value"]["directions"].values())
    # plan: the build plans of the next step use it
    outside = ("algorithm.schemaVersion", "algorithm.family", "algorithm.id", "algorithm.common.", "plan.")
    unused = []
    for path, node in _terms():
        if path.startswith(outside) or node.get(DERIVED):
            continue
        justified = node.get(UNUSED) or {}
        if path not in used and not isinstance(justified, str):
            unused.append(path)
        unused += [f"{path} {v}" for v in node.get(VALUES) or {} if v not in used[path] and v not in justified]
    assert unused == []


def _groups() -> dict:
    return yaml.safe_load(GROUPS.read_text())


def _group_words() -> dict:
    """Each group.* word groups.yaml holds, and each the read tools return about a group."""
    from perfrepair.catalog.views import get_group, list_groups
    doc, words = _groups(), defaultdict(set)
    for key in doc:
        words[f"group.{key}"].add(None)
    for group, raw in doc["groups"].items():
        words["group.family"].add(group)
        words[f"group.{group}"].add(None)
        for key in raw:
            words[f"group.{key}"].add(None)
    returned = {k for g in list_groups() for k in g} | set(get_group(next(iter(doc["groups"]))))
    for key in returned:
        words[f"group.{key}"].add(None)
    return words


def test_each_family_word_means_exactly_its_families_yaml_description():
    families = Families.load()
    assert {f.id: f.description for f in [*families.all, families.unidentified]} == what_is("group.family")["values"]


@pytest.mark.parametrize("path,value", [
    ("algorithm.contract.input.passwordBased", 1), ("algorithm.conditions.authenticated.value", 0),
    ("algorithm.conditions.wrapOnly.value", 1), ("algorithm.contract.input.wrap", 0)])
def test_a_closed_boolean_refuses_one_and_zero(path, value):
    with pytest.raises(GlossaryError, match="no value"):
        what_is(path, value)


def test_groups_yaml_holds_only_glossary_words_and_its_ids_fit():
    doc = _groups()
    words = what_is("group")
    assert set(doc) <= set(words)
    for group, raw in doc["groups"].items():
        assert what_is("group.family", group)
        assert set(raw) <= {"algorithms", "exemplars"}
        for i in [*raw["algorithms"], *raw["exemplars"]]:
            assert what_is("group.algorithms", i)


def test_each_exemplar_is_a_member_of_its_group():
    for group, raw in _groups()["groups"].items():
        assert [e for e in raw["exemplars"] if e not in raw["algorithms"]] == [], group


def test_a_new_entry_with_an_unlisted_term_is_refused_naming_the_term():
    from perfrepair.catalog.algorithms import Entry, algorithms
    from perfrepair.catalog.groups import group_catalog
    from perfrepair.validation.catalogue_entry import entry_check
    catalogue, families = algorithms(), Families.load()
    entry = catalogue.of("digest.none", "MessageDigest|MD5")
    assert entry_check(entry, catalogue, group_catalog(), families) == []
    bad = Entry(entry.id, entry.family, {**entry.raw, "required": [{"name": "colour", "source": "inferred"}]})
    swapped = type(catalogue)(tuple(bad if e.id == entry.id else e for e in catalogue.entries), catalogue.common)
    assert any("algorithm.required.name: no value 'colour'" in p for p in entry_check(bad, swapped, group_catalog(), families))


def test_common_is_in_the_glossary():
    common = yaml.safe_load(COMMON.read_text())
    assert set(common) <= {*what_is("algorithm.common"), "schemaVersion"}
    for name, row in common["keyStrength"].items():
        assert what_is("algorithm.sourcedOnly.value.key", name)
        assert set(row) <= {"source", "bits"}


def test_every_family_has_its_word():
    assert {f.id for f in Families.load().all} | {"unidentified"} == set(what_is("group.family")["values"])


@pytest.mark.parametrize("change,word", [
    (lambda d: d.update(colour=1), "build.colour"),
    (lambda d: next(iter(d["builds"].values())).update(colour=1), "build.colour"),
    (lambda d: next(iter(d["builds"].values())).update(origin="colour"), "no value 'colour'"),
    (lambda d: d["builds"].update({"BC 1.79": {"name": "BC", "selfReported": "1.79", "origin": "host"}}), "not <name> @ <build>")])
def test_provider_builds_is_closed_at_load(tmp_path, change, word):
    doc = yaml.safe_load(PROVIDER_BUILDS.read_text())
    change(doc)
    path = tmp_path / "provider-builds.yaml"
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(ProviderBuildError, match=word):
        load_builds(path)


@pytest.mark.parametrize("change,word", [
    (lambda d: d.update(colour=1), "names.colour"),
    (lambda d: d["names"].update(Colour={"A": []}), "no value 'Colour'"),
    (lambda d: d["sized"]["Cipher"]["AES_128"].update(colour=1), "names.sized.colour"),
    (lambda d: d["transformations"]["Cipher"].update(colour=[]), "names.transformations.colour")])
def test_algorithm_names_is_closed_at_load(tmp_path, change, word):
    doc = yaml.safe_load(NAMES_FILE.read_text())
    change(doc)
    path = tmp_path / "algorithm-names.yaml"
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(NamesError, match=word):
        Names.load(path)


@pytest.mark.parametrize("value,fits", [("same", True), ("any", True), ("pad:16", True), ("plus:8", True), ("fixed:256", True), ("anyX", False), ("pad:", False), ("pad:0", False), ("fixed:256X", False)])
def test_a_formula_has_one_form(value, fits):
    if fits:
        assert what_is("algorithm.conditions.output.formula", value)
    else:
        with pytest.raises(GlossaryError):
            what_is("algorithm.conditions.output.formula", value)


def test_a_role_goes_only_to_engine_types_that_exist():
    types = Families.load().types
    assert {e for r in roles().values() for e in r.get("goesTo", {})} <= types
