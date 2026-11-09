"""A name a person moves out of `unidentified` into a family is identified from then on: no model call, no key evidence."""
import shutil

import pytest
import yaml

from cryptobench.catalogue import groups as groups_module
from cryptobench.catalogue.algorithms import DIRECTORY, load as load_catalogues
from cryptobench.catalogue.families import UNIDENTIFIED, Families
from cryptobench.catalogue.groups import CATALOG, GroupsError, load
from cryptobench.catalogue.names import CATALOG as NAMES_CATALOG, Names
from perfrepair.catalog.screening import Screening
from perfrepair.data_handler.inbound.probe import Probe
from perfrepair.grouping.build.items import build
from perfrepair.probe import identified as identified_module
from perfrepair.probe.identified import identified
from perfrepair.screen.groups import code_groups
from perfrepair.screen.stage import screen_items

NAME, ID = "MOVED-ALG", "Cipher|MOVED-ALG"
FAMILIES = Families.load()
PROBE = Probe({"providers": [{"name": "P", "precedence": 1, "services": [{"type": "Cipher", "algorithm": NAME}]}]})
# no key evidence: the trial failed and the service declares no key format
TRIAL = {"services": [{"provider": "P", "type": "Cipher", "algorithm": NAME, "instantiates": True,
                       "defaultRun": {"works": False, "error": "no provider generates it"}}]}


@pytest.fixture
def catalogs(tmp_path):
    """Copies of the names, groups and catalogues: the name is known to none of them yet."""
    names = yaml.safe_load(NAMES_CATALOG.read_text())
    names["names"]["Cipher"][NAME] = []
    names_path = tmp_path / "names.yaml"
    names_path.write_text(yaml.safe_dump(names))
    shutil.copytree(DIRECTORY, tmp_path / "algorithms")
    return tmp_path, Names.load(names_path)


def _catalog(tmp_path, family: str, entry: dict | None):
    doc = yaml.safe_load(CATALOG.read_text())
    doc["groups"][family]["algorithms"].append(ID)
    path = tmp_path / f"groups-{family}.yaml"
    path.write_text(yaml.safe_dump(doc))
    if entry is not None:
        file = tmp_path / "algorithms" / f"{family}_catalogue.yaml"
        catalogue = yaml.safe_load(file.read_text())
        catalogue["algorithms"][ID] = entry
        file.write_text(yaml.safe_dump(catalogue))
    return load(path, FAMILIES, _names(tmp_path), load_catalogues(tmp_path / "algorithms", FAMILIES))


def _names(tmp_path) -> Names:
    return Names.load(tmp_path / "names.yaml")


ENTRY = {"required": [], "optional": [], "conditions": {}, "lifecycle": {"reset": {"forward": {"value": "afterInit", "source": "inferred"}, "reverse": {"value": "afterInit", "source": "inferred"}}}, "operations": {"value": ["encrypt", "decrypt"], "source": "inferred"}, "sourcedOnly": [], "providers": {}, "provenance": {"by": "person"},
         "contract": {"key": "app", "input": {"passwordBased": False, "wrap": False},
                      "output": {"base": "MOVED", "mode": "ECB", "padding": "NOPADDING"}}}


def _run(catalog, names, monkeypatch):
    monkeypatch.setattr(identified_module, "group_catalog", lambda: catalog)
    monkeypatch.setattr(groups_module, "group_catalog", lambda: catalog)
    items, profiles = build(PROBE, names, TRIAL, FAMILIES, catalog=catalog)
    verdicts = screen_items(Screening.load(names=names), names, items, profiles)
    return items[0], profiles, verdicts


def test_a_name_in_no_list_and_without_evidence_is_unidentified_and_asked(catalogs, monkeypatch):
    tmp_path, names = catalogs
    item, profiles, verdicts = _run(load(CATALOG, FAMILIES, names), names, monkeypatch)
    assert (item.family, profiles[item.id].keyKind, profiles[item.id].keyKindFrom) == (UNIDENTIFIED, "unknown", "none")
    assert not identified(item, verdicts)


def test_a_name_held_in_unidentified_stays_there(catalogs, monkeypatch):
    tmp_path, names = catalogs
    item, profiles, _ = _run(_catalog(tmp_path, UNIDENTIFIED, None), names, monkeypatch)
    assert (item.family, profiles[item.id].keyKindFrom) == (UNIDENTIFIED, "catalogue")


def test_moved_out_of_unidentified_it_is_identified_without_a_model(catalogs, monkeypatch):
    tmp_path, names = catalogs
    catalog = _catalog(tmp_path, "cipher.secret", ENTRY)
    item, profiles, verdicts = _run(catalog, names, monkeypatch)
    assert (item.family, profiles[item.id].keyKind, profiles[item.id].keyKindFrom) == ("cipher.secret", "secret", "catalogue")
    assert identified(item, verdicts)
    placed = code_groups([item], verdicts, profiles)
    assert [g.members for g in placed.values()] == [[item.id]] and list(placed) == [catalog.of("cipher.secret", NAME).id]


def test_one_id_in_a_family_and_in_unidentified_is_refused(tmp_path):
    doc = yaml.safe_load(CATALOG.read_text())
    doc["groups"][UNIDENTIFIED]["algorithms"].append("MessageDigest|MD5")
    path = tmp_path / "groups.yaml"
    path.write_text(yaml.safe_dump(doc))
    with pytest.raises(GroupsError, match="listed in a family and in unidentified"):
        load(path)


def test_the_group_exists_and_holds_nothing_for_now():
    assert load(CATALOG).unidentified == ()
    assert yaml.safe_load(CATALOG.read_text())["groups"][UNIDENTIFIED] == {"exemplars": [], "algorithms": []}
