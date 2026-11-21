import json
from pathlib import Path

import pytest

from cryptobench.shared import paths
from cryptobench.shared.settings import authored, bundled

# the cases Kotlin's BesideAuthoredParityTest reads too
BESIDE = json.loads((paths.repo().contract_documents / "beside-authored.json").read_text())


def read(tmp_path, text):
    (tmp_path / "global.yaml").write_text(text)
    return authored.read(tmp_path / "global.yaml")


def test_the_named_files_are_against_the_global_file(tmp_path):
    given = read(tmp_path, "selection: {testSet: sets/a.yaml, knownVectors: ~/mine.yaml}\n")
    assert given.test_set == tmp_path / "sets/a.yaml"
    assert given.known_vectors == Path.home() / "mine.yaml"


@pytest.mark.parametrize("case", BESIDE["cases"], ids=lambda case: case["value"])
def test_the_test_set_path_is_kotlins_beside_authored(case):
    assert str(paths.beside(BESIDE["settingsFile"], case["value"])) == case["path"]
    given = authored.Authored(Path(BESIDE["settingsFile"]), {"selection": {"testSet": case["value"]}})
    assert str(given.test_set) == case["path"]


def test_nothing_named_is_none_and_no_bundled(tmp_path):
    given = read(tmp_path, "schemaVersion: 1\n")
    assert (given.test_set, given.known_vectors, given.bundled) == (None, None, [])


def test_a_bad_bundled_list_is_refused_only_where_it_is_read(tmp_path):
    given = read(tmp_path, "schemaVersion: 1\nselection: {testSet: a.yaml}\nproviders: {bundled: [{create: a.B}]}\n")
    assert given.test_set == tmp_path / "a.yaml"
    with pytest.raises(bundled.BundledError, match="^wrong_type: providers.bundled in "):
        given.bundled


def test_a_missing_global_file_is_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        authored.read(tmp_path / "absent.yaml")
