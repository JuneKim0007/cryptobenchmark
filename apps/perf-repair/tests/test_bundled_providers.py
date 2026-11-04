"""The bundled-providers catalog: the packaged file loads, agrees with libraries.yaml, and each bad row is one problem."""
import pytest
import yaml

from perfrepair.app.facts.dependencies import read_libraries
from perfrepair.catalog.bundled_providers import BundledCatalog, BundledCatalogError, BundledRow, catalog_problems

ROW = {"artifact": "g:a", "provider": "Aaa", "create": "g.Aaa#make", "source": "S"}


def doc(*rows):
    return {"schemaVersion": 1, "sources": {"S": "https://example.org"}, "providers": list(rows)}


def test_the_packaged_catalog_loads():
    rows = BundledCatalog.load().rows
    assert rows and all(r.source for r in rows.values())


def test_each_row_names_the_provider_libraries_yaml_gives_its_artifact():
    libraries = read_libraries()
    for artifact, row in BundledCatalog.load().rows.items():
        group, name = artifact.split(":")
        hit = next(lib for lib in libraries if lib.group == group and name.startswith(lib.name))
        assert hit.providerName == row.provider, artifact


def test_a_row_entry_carries_the_apps_version_and_its_alias():
    assert BundledRow("g:a", "Aaa", "g.Aaa", "S", alias="Bundled").entry("1.2") == {
        "artifact": "g:a:1.2", "create": "g.Aaa", "alias": "Bundled"}


@pytest.mark.parametrize("change, problem", [
    ({"artifact": "g:a:1"}, "artifact 'g:a:1' is not group:name"),
    ({"create": "Aaa"}, "create 'Aaa' is not Class or Class#factory"),
    ({"alias": "a b"}, "alias 'a b' is not a name without whitespace"),
    ({"minSdk": 0}, "minSdk 0 is not a positive integer"),
    ({"minSdk": True}, "minSdk True is not a positive integer"),
    ({"blocked": " "}, "blocked is blank"),
    ({"source": "T"}, "source 'T' is not in sources"),
    ({"version": "1"}, "unknown key version"),
    ({"create": None}, "no create"),
])
def test_a_bad_row_is_one_problem(change, problem):
    assert catalog_problems(doc({**ROW, **change})) == [f"providers[0]: {problem}"]


def test_a_duplicate_artifact_is_a_problem_a_shared_alias_is_not():
    assert catalog_problems(doc({**ROW, "alias": "X"}, {**ROW, "alias": "X"})) == ["duplicate artifact g:a"]
    assert catalog_problems(doc({**ROW, "alias": "X"}, {**ROW, "artifact": "g:b", "alias": "X"})) == []


def test_a_bad_file_raises_every_problem_at_once(tmp_path):
    path = tmp_path / "b.yaml"
    path.write_text(yaml.safe_dump(doc({**ROW, "create": "Aaa", "minSdk": -1})))
    with pytest.raises(BundledCatalogError, match="create 'Aaa'.*minSdk -1"):
        BundledCatalog.load(path)
    path.write_text("schemaVersion: 2\n")
    with pytest.raises(BundledCatalogError, match="schemaVersion is not 1"):
        BundledCatalog.load(path)
