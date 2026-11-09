"""recipes.yaml: each recipe one form, its arguments typed and nested recipes present; a catalogue row names a recipe that passes its role."""
import shutil

import pytest
import yaml

from cryptobench.catalogue.algorithms import DIRECTORY, AlgorithmsError, algorithms, load
from cryptobench.catalogue.recipes import RecipeError, load as load_recipes, recipes


def test_the_packaged_recipes_load_and_every_one_a_row_names():
    rows = [r for e in algorithms().entries for r in [*e.raw["required"], *(v for o in e.raw["providers"].values() for v in o.values())]]
    named = {r["recipe"] for r in rows if isinstance(r, dict) and "recipe" in r}
    nested = {a["recipe"] for r in recipes().by_id.values() for a in r.get("args") or [] if a.get("kind") == "recipe"}
    assert set(recipes().by_id) == named | nested


def test_roles_include_those_of_a_nested_recipe():
    assert recipes().roles("jca.pssSpec") == {"digest", "mgf1", "saltBytes"}


@pytest.mark.parametrize("raw,code", [
    ({"class": "a.b.C", "builder": "x"}, "none of the forms"),
    ({"class": "a.b.C", "args": [{"kind": "recipe", "recipe": "jca.nope"}]}, "no recipe"),
    ({"class": "a.b.C", "args": [{"kind": "constant", "role": "iv", "value": 1}]}, "holds a value and no role"),
    ({"class": "a.b.C", "args": [{"kind": "bytes"}]}, "names its role")])
def test_a_bad_recipe_is_refused(tmp_path, raw, code):
    path = tmp_path / "recipes.yaml"
    path.write_text(yaml.safe_dump({"schemaVersion": 1, "recipes": {"x.bad": raw}}))
    with pytest.raises(RecipeError, match=f"recipes_invalid: .*{code}"):
        load_recipes(path)


@pytest.mark.parametrize("row,code", [
    ({"name": "iv", "recipe": "jca.nope", "passedTo": "init", "source": "inferred"}, "is no recipe"),
    ({"name": "salt", "recipe": "jca.ivSpec", "passedTo": "init", "source": "inferred"}, "passes no such role")])
def test_a_row_naming_an_unknown_recipe_or_one_without_its_role_is_refused(tmp_path, row, code):
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    path = target / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"]["Cipher|AES/CBC/PKCS5Padding"]["required"].append(row)
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match=code):
        load(target)
