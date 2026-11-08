import pytest

from perfrepair.dto.prompt import CorrectionPrompt
from perfrepair.ai.runtime.prompt import PromptError, PromptLibrary
from perfrepair.ai.runtime.prompt.library import PACKAGED


def test_packaged_prompts_load_and_fill_only_declared_values():
    library = PromptLibrary.load()
    assert library.system("parse/algorithm-classify").text == (PACKAGED / "parse" / "algorithm-classify.system.md").read_text()
    filled = library.system("parse/grouping-assign", id_pattern="P", max_description=9).text
    assert "{id_pattern}" not in filled and "{max_description}" not in filled


def test_the_charter_corrects_with_the_rejection_template():
    correction = PromptLibrary.load().charter("parse/algorithm-classify", {}).correct(["a", "b"])
    assert isinstance(correction, CorrectionPrompt) and "- a" in correction.text and "- b" in correction.text


def test_values_and_lifetimes_are_checked():
    library = PromptLibrary.load()
    with pytest.raises(PromptError, match="value_mismatch"):
        library.system("parse/grouping-assign", id_pattern="P")
    with pytest.raises(PromptError, match="lifetime_mismatch"):
        library.system("shared/rejection", problems="x")
    with pytest.raises(PromptError, match="prompt_unknown"):
        library.system("nope")


def test_an_override_replaces_by_file_name_and_rejects_strays(tmp_path):
    (tmp_path / "parse").mkdir()
    (tmp_path / "parse" / "algorithm-classify.system.md").write_text("mine")
    library = PromptLibrary.load(tmp_path)
    assert library.system("parse/algorithm-classify").text == "mine" and library.source("parse/algorithm-classify") == tmp_path / "parse" / "algorithm-classify.system.md"
    (tmp_path / "parse" / "algorithm-clasify.system.md").write_text("typo")
    with pytest.raises(PromptError, match="prompt_unknown"):
        PromptLibrary.load(tmp_path)


def test_an_override_must_keep_declared_placeholders(tmp_path):
    (tmp_path / "parse").mkdir()
    (tmp_path / "parse" / "grouping-assign.system.md").write_text("no placeholders")
    with pytest.raises(PromptError, match="placeholder_missing"):
        PromptLibrary.load(tmp_path)


def test_the_fingerprint_moves_with_every_run_element(tmp_path):
    library = PromptLibrary.load()
    base = library.charter("parse/algorithm-classify", {"x": 1, "y": 2})
    assert base.fingerprint == library.charter("parse/algorithm-classify", {"y": 2, "x": 1}).fingerprint
    assert base.fingerprint != library.charter("parse/algorithm-classify", {"x": 2}).fingerprint
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "rejection.turn.md").write_text("again: {problems}")
    assert base.fingerprint != PromptLibrary.load(tmp_path).charter("parse/algorithm-classify", {"x": 1, "y": 2}).fingerprint


def test_a_charter_records_each_prompt_source_and_hashes_none_of_them(tmp_path):
    (tmp_path / "parse").mkdir()
    (tmp_path / "parse" / "algorithm-classify.system.md").write_text((PACKAGED / "parse" / "algorithm-classify.system.md").read_text())
    packaged = PromptLibrary.load().charter("parse/algorithm-classify", {})
    copied = PromptLibrary.load(tmp_path).charter("parse/algorithm-classify", {})
    assert dict(packaged.sources) == {"parse/algorithm-classify": "packaged", "shared/rejection": "packaged"}
    assert dict(copied.sources)["parse/algorithm-classify"] == str(tmp_path / "parse" / "algorithm-classify.system.md")
    assert packaged.fingerprint == copied.fingerprint and packaged == copied
