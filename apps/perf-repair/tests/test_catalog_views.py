"""An agent's view of one entry holds only its provider build's facts; the group reads hold exactly what groups.yaml holds."""
import json
import shutil

import pytest
import yaml

from perfrepair.catalog.algorithms import DIRECTORY, Algorithms, AlgorithmsError, Entry, algorithms, load
from perfrepair.catalog.families import Families
from perfrepair.catalog.groups import CATALOG as GROUPS
from perfrepair.catalog.overrides import apply_override
from perfrepair.catalog.provider_builds import ProviderBuildError, provider_builds
from perfrepair.catalog.views import get_group, list_groups, view_for

GCM = "Cipher|AES/GCM/NoPadding"
TAG = {"name": "tagBits", "accepted": [96, 104, 112, 120, 128], "default": 128, "source": "measured"}
BC_TAGS = [32, 64, 96, 104, 112, 120, 128]
BC, OPENSSL = "BC @ android-26", "AndroidOpenSSL @ android-33"
OTHER = {OPENSSL: {"optional.tagBits.default": 7777}, "SunJCE @ jdk-25": {"conditions.output.bytes": 8888}}


def apply_overrides(entry: dict, overrides: dict) -> dict:
    for path, value in overrides.items():
        apply_override(entry, path, value)
    return entry


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
    doc["algorithms"][GCM]["providers"] = {BC: {"optional.tagBits.accepted": BC_TAGS}, **OTHER}
    path.write_text(yaml.safe_dump(doc))
    return target


def _no_other_provider(view: dict, keep: str | None):
    text = json.dumps(view)
    assert "providers" not in view
    assert not any(p in text for p in [*OTHER, BC] if p != keep)
    assert "7777" not in text and "8888" not in text


def test_bc_sees_its_tag_lengths_and_no_other_provider(with_providers):
    catalogue = load(with_providers)
    expected = {k: v for k, v in _yaml_entry(with_providers, "cipher.secret", GCM).items() if k != "providers"}
    expected = apply_overrides(expected, catalogue.of("cipher.secret", GCM).raw["providers"][BC])
    view = view_for(GCM, BC, catalogue)
    assert view == expected and next(r for r in view["optional"] if r["name"] == "tagBits")["accepted"] == BC_TAGS
    _no_other_provider(view, BC)


@pytest.mark.parametrize("provider", ["NoSuchProvider", "BC", "bc 1.79", "BC 1.79", "AndroidOpenSSL", "AndroidOpenSSL @ android-99"])
def test_an_unknown_or_ambiguous_build_is_refused_never_the_base_entry(with_providers, provider):
    with pytest.raises(ProviderBuildError, match="provider_build_unknown"):
        view_for(GCM, provider, load(with_providers))


def test_no_provider_is_the_base_entry(with_providers):
    expected = {k: v for k, v in _yaml_entry(with_providers, "cipher.secret", GCM).items() if k != "providers"}
    assert view_for(GCM, None, load(with_providers)) == expected
    _no_other_provider(view_for(GCM, None, load(with_providers)), None)


def test_a_name_one_build_carries_maps_to_its_key():
    assert provider_builds().resolve("BundledBC") == "BundledBC @ org.bouncycastle:bcprov-jdk18on:1.79"
    assert provider_builds().resolve("BundledConscrypt") == "BundledConscrypt @ org.conscrypt:conscrypt-android:2.5.3"


def test_a_catalogue_key_outside_the_build_list_is_refused(with_providers):
    path = with_providers / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"][GCM]["providers"] = {"BC 1.81": {"optional.tagBits.accepted": [128]}}
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="no build of provider-builds.yaml"):
        load(with_providers)


def test_a_build_can_drop_or_add_a_whole_row():
    bits = view_for("Cipher|PBEWithHmacSHA256AndAES_256", OPENSSL)
    assert {r["name"] for r in bits["required"]} >= {"secretKey", "iv", "input"}
    assert not {"password", "salt", "iterationCount"} & {r["name"] for r in bits["required"]}
    assert view_for("Cipher|PBEWithHmacSHA256AndAES_256")["contract"]["key"] == "password"
    assert bits["contract"]["key"] == "app" and bits["contract"]["output"] == {"base": "AES", "mode": "CBC", "padding": "PKCS5Padding"}


@pytest.mark.parametrize("family,identifier", [
    ("digest.none", "MessageDigest|SHA-256"), ("signature.pair", "Signature|SHA256withRSA/PSS"),
    ("cipher.secret", "Cipher|PBEWithHmacSHA1AndAES_128"), ("keypairgen.none", "KeyPairGenerator|XWING")])
def test_a_real_entry_is_its_yaml_without_the_providers_section(family, identifier):
    expected = {k: v for k, v in _yaml_entry(DIRECTORY, family, identifier).items() if k != "providers"}
    expected = apply_overrides(expected, algorithms().of(family, identifier).raw["providers"].get(OPENSSL) or {})
    assert view_for(identifier, OPENSSL) == expected


def test_a_view_is_a_copy_the_caller_cannot_change_the_catalogue_through(with_providers):
    catalogue = load(with_providers)
    view_for(GCM, BC, catalogue)["optional"][0]["accepted"].append(1)
    assert view_for(GCM, BC, catalogue)["optional"][0]["accepted"] == BC_TAGS


def test_an_unknown_id_is_a_coded_error():
    with pytest.raises(AlgorithmsError, match="algorithm_unknown: .*in no catalogue"):
        view_for("Cipher|NOPE")


def test_an_id_in_two_catalogues_is_a_coded_error():
    catalogue, wrap = algorithms(), "Cipher|DESedeWrap"
    entry = catalogue.of("cipher.secret", wrap)
    twice = Algorithms((*catalogue.entries, Entry(entry.id, "cipher.pair", entry.raw)), catalogue.common)
    assert view_for(wrap) == {k: v for k, v in entry.raw.items() if k != "providers"}
    with pytest.raises(AlgorithmsError, match="algorithm_unknown: .*in 2 catalogues"):
        view_for(wrap, None, twice)


def test_an_override_naming_no_field_is_refused(tmp_path, with_providers):
    path = with_providers / "cipher.secret_catalogue.yaml"
    doc = yaml.safe_load(path.read_text())
    doc["algorithms"][GCM]["providers"] = {"BC": {"optional.nonesuch.accepted": [1]}}
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(AlgorithmsError, match="names no field"):
        load(with_providers)


def test_list_groups_is_exactly_each_group_s_id_description_and_exemplars():
    families, doc = Families.load(), yaml.safe_load(GROUPS.read_text())["groups"]
    assert list_groups() == [{"id": g, "description": families.by_id[g].description, "exemplars": raw["exemplars"]} for g, raw in doc.items()]


def test_get_group_returns_the_yaml_s_members_a_page_at_a_time():
    ids = yaml.safe_load(GROUPS.read_text())["groups"]["cipher.pair"]["algorithms"]
    first = get_group("cipher.pair", items=3)
    assert first == {"id": "cipher.pair", "members": ids[:3], "remaining": len(ids) - 3}
    assert get_group("cipher.pair", items=3, after=first["members"][-1])["members"] == ids[3:6]
    assert get_group("cipher.pair", items=len(ids)) == {"id": "cipher.pair", "members": ids, "remaining": 0}
    assert get_group("cipher.pair")["members"] == ids[:10]


def test_the_unidentified_group_reads_like_any_other_and_holds_nothing():
    assert get_group("unidentified") == {"id": "unidentified", "members": [], "remaining": 0}


@pytest.mark.parametrize("group,after", [("cipher.nope", None), ("cipher.pair", "Cipher|NOPE")])
def test_an_unknown_group_or_cursor_is_a_coded_error(group, after):
    with pytest.raises(AlgorithmsError, match="algorithm_unknown"):
        get_group(group, after=after)


@pytest.mark.parametrize("items", [0, -1, 2.5, True, "3"])
def test_get_group_refuses_a_page_size_below_one(items):
    with pytest.raises(AlgorithmsError, match="algorithm_unknown: items"):
        get_group("cipher.pair", items=items)


def test_get_group_reads_the_cursor_case_folded_like_view_for():
    ids = yaml.safe_load(GROUPS.read_text())["groups"]["cipher.pair"]["algorithms"]
    assert get_group("cipher.pair", items=2, after=ids[0].upper())["members"] == ids[1:3]
