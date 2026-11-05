"""An agent's view of one entry holds only its provider's facts; a group view only the description and ids."""
import json
import shutil

import pytest
import yaml

from perfrepair.catalog.algorithms import DIRECTORY, AlgorithmsError, load
from perfrepair.catalog.families import Families
from perfrepair.catalog.groups import CATALOG as GROUPS
from perfrepair.catalog.views import group_view, view_for

GCM = "Cipher|AES/GCM/NoPadding"
TAG = {"name": "tagBits", "accepted": [96, 104, 112, 120, 128], "default": 128, "source": "measured"}
BC_TAGS = [32, 64, 96, 104, 112, 120, 128]
OTHER = {"AndroidOpenSSL": {"optional.tagBits.default": 7777}, "SunJCE": {"conditions.output.bytes": 8888}}


def _yaml_entry(directory, family: str, identifier: str) -> dict:
    return yaml.safe_load((directory / f"{family}_catalogue.yaml").read_text())["algorithms"][identifier]


@pytest.fixture
def with_providers(tmp_path):
    """The real catalogues with a BC tag-length difference, and two other providers' facts, on the GCM entry."""
    target = tmp_path / "algorithms"
    shutil.copytree(DIRECTORY, target)
    path = target / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"][GCM]["optional"] = [TAG]
    doc["algorithms"][GCM]["providers"] = {"BC": {"optional.tagBits.accepted": BC_TAGS}, **OTHER}
    path.write_text(yaml.safe_dump(doc))
    return target


def _no_other_provider(view: dict, keep: str | None):
    text = json.dumps(view)
    assert "providers" not in view
    assert not any(p in text for p in [*OTHER, "BC"] if p != keep)
    assert "7777" not in text and "8888" not in text


def test_bc_sees_its_tag_lengths_and_no_other_provider(with_providers):
    expected = {k: v for k, v in _yaml_entry(with_providers, "cipher.secret", GCM).items() if k != "providers"}
    expected["optional"][0]["accepted"] = BC_TAGS
    view = view_for(GCM, "BC", load(with_providers))
    assert view == expected
    _no_other_provider(view, "BC")


def test_an_unknown_provider_sees_the_base_entry(with_providers):
    expected = {k: v for k, v in _yaml_entry(with_providers, "cipher.secret", GCM).items() if k != "providers"}
    view = view_for(GCM, "NoSuchProvider", load(with_providers))
    assert view == expected and view["optional"][0]["accepted"] == TAG["accepted"]
    _no_other_provider(view, None)


@pytest.mark.parametrize("family,identifier", [
    ("digest.none", "MessageDigest|SHA-256"), ("signature.pair", "Signature|SHA256withRSA/PSS"),
    ("cipher.unknown", "Cipher|PBEWithHmacSHA1AndAES_128"), ("keypairgen.none", "KeyPairGenerator|XWING")])
def test_a_real_entry_is_its_yaml_without_the_providers_section(family, identifier):
    expected = {k: v for k, v in _yaml_entry(DIRECTORY, family, identifier).items() if k != "providers"}
    assert view_for(identifier, "AndroidOpenSSL") == expected


def test_a_view_is_a_copy_the_caller_cannot_change_the_catalogue_through(with_providers):
    catalogue = load(with_providers)
    view_for(GCM, "BC", catalogue)["optional"][0]["accepted"].append(1)
    assert view_for(GCM, "BC", catalogue)["optional"][0]["accepted"] == BC_TAGS


@pytest.mark.parametrize("identifier,where", [("Cipher|NOPE", "in no catalogue"), ("Cipher|DESedeWrap", "in 2 catalogues")])
def test_an_unknown_or_ambiguous_id_is_a_coded_error(identifier, where):
    with pytest.raises(AlgorithmsError, match=f"algorithm_unknown: .*{where}"):
        view_for(identifier, "BC")


def test_an_override_naming_no_field_is_refused(tmp_path, with_providers):
    path = with_providers / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"][GCM]["providers"] = {"BC": {"optional.nonesuch.accepted": [1]}}
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="names no field"):
        load(with_providers)


def test_a_group_view_is_the_family_description_and_its_ids_only():
    families = Families.load()
    ids = yaml.safe_load(GROUPS.read_text())["groups"]["cipher.pair"]["algorithms"]
    assert group_view("cipher.pair") == {"description": families.by_id["cipher.pair"].description, "algorithms": ids}
    with pytest.raises(AlgorithmsError, match="algorithm_unknown"):
        group_view("cipher.nope")
