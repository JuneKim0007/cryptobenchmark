"""app/facts/target_set.py: root and path entries, inline or a targets file, merged by path then applicationId."""
import pytest
import yaml
from perfrepair.app.facts.target_set import TARGETS_SCHEMA_VERSION, resolve_targets
from perfrepair.stop.halt import Coded
from test_app_kind import tree


def app(root, app_id="x.app"):
    return tree(root, {"settings.gradle": "", "app/build.gradle": f"apply plugin: 'com.android.application'\n"
                       f"android {{ defaultConfig {{ applicationId '{app_id}' }} }}\n"})


def lib(root):
    return tree(root, {"build.gradle": "plugins { id 'com.android.library' }\n", "src/main/AndroidManifest.xml": "<manifest/>"})


@pytest.fixture
def corpus(tmp_path):
    base = tmp_path / "corpus"
    app(base / "one", "x.one")
    lib(base / "proj" / "lib-common")
    app(base / "proj" / "client", "x.client")
    tree(base / "readme", {"README.md": "x"})
    tree(base / "manifest", {"AndroidManifest.xml": "<manifest/>"})
    return base


def settings(tmp_path):
    return tmp_path / "perfrepair.yaml"


def test_a_root_finds_its_apps_and_records_the_rest(tmp_path, corpus):
    found = resolve_targets([{"root": "corpus", "perfMode": ["latency"]}], settings(tmp_path))
    assert [t.path.name for t in found.apps] == ["one", "client"]
    assert all(t.perfMode.name == "latency" and t.entry == {"root": str(corpus)} for t in found.apps)
    assert {(s.path.name, s.kind, s.reason, s.stops) for s in found.skipped} == {
        ("lib-common", "library", "library", False), ("manifest", "unknown_layout", "manifest_only", False)}
    assert not found.warnings


def test_a_root_without_an_app_is_a_warning(tmp_path):
    lib(tmp_path / "libs" / "a")
    found = resolve_targets([{"root": "libs"}], settings(tmp_path))
    assert not found.apps and found.warnings == [
        f"apps.targets root {(tmp_path / 'libs').resolve()} holds no app (1 candidates, none an app)"]


def test_a_path_is_exactly_that_folder_a_library_allowed_and_a_non_app_a_stop(tmp_path, corpus):
    outside = app(tmp_path / "elsewhere", "x.out")
    found = resolve_targets([str(outside), {"path": "corpus/proj/lib-common"}, "corpus/readme", "nope"], settings(tmp_path))
    assert [(t.path.name, t.kind.kind) for t in found.apps] == [("elsewhere", "app"), ("lib-common", "library")]
    assert [(s.path.name, s.kind, s.stops) for s in found.skipped] == [("readme", "not_android", True), ("nope", "missing", True)]


def test_duplicates_merge_by_path_then_by_application_id(tmp_path, corpus):
    copy = app(tmp_path / "copy", "x.one")
    found = resolve_targets([{"path": "corpus/one", "perfMode": "all"}, {"root": "corpus"}, str(copy)], settings(tmp_path))
    one = (corpus / "one").resolve()
    assert [t.path.name for t in found.apps] == ["one", "client"] and found.apps[0].perfMode.name == "generic"
    dups = [(s.path, s.reason) for s in found.skipped if s.reason.startswith("duplicate_of")]
    assert dups == [(one, f"duplicate_of: {one}"), (copy.resolve(), f"duplicate_of: {one}")]


def test_a_targets_file_resolves_its_paths_against_its_own_folder(tmp_path, corpus):
    (tmp_path / "lists").mkdir()
    (tmp_path / "lists" / "targets.yaml").write_text(yaml.safe_dump([{"root": "../corpus/proj"}, "../corpus/one"]))
    found = resolve_targets("lists/targets.yaml", settings(tmp_path))
    assert [t.path.name for t in found.apps] == ["client", "one"]


def test_a_bad_or_missing_targets_file_is_a_coded_error(tmp_path):
    with pytest.raises(Coded, match="^missing_file: apps.targets file "):
        resolve_targets("absent.yaml", settings(tmp_path))
    (tmp_path / "bad.yaml").write_text("- {name: x}\n")
    with pytest.raises(Coded, match="^invalid: apps.targets file "):
        resolve_targets("bad.yaml", settings(tmp_path))


def test_the_document_lists_every_app_and_skip(tmp_path, corpus):
    doc = resolve_targets([{"root": "corpus"}], settings(tmp_path)).document()
    assert doc["schemaVersion"] == TARGETS_SCHEMA_VERSION
    assert doc["apps"][1] == {"path": str((corpus / "proj" / "client").resolve()), "kind": "app",
                              "applicationId": "x.client", "entry": {"root": str(corpus)}, "perfMode": None}
    assert {"path", "kind", "reason", "entry"} == set(doc["skipped"][0])
