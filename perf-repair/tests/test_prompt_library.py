import pytest

from perfrepair.dto.prompt import CorrectionPrompt, Lifetime, Prompt, SystemPrompt, TaskPrompt, fingerprint
from perfrepair.orchestrate.engine.ask import rejection
from perfrepair.orchestrate.prompt import PromptError, PromptLibrary
from perfrepair.orchestrate.prompt.library import PACKAGED


def test_each_element_carries_its_lifetime():
    assert (SystemPrompt.lifetime, TaskPrompt.lifetime, CorrectionPrompt.lifetime) == (Lifetime.RUN, Lifetime.SESSION, Lifetime.TURN)
    with pytest.raises(TypeError):
        Prompt("x", "y")


def test_packaged_prompts_load_and_fill_only_declared_values():
    library = PromptLibrary.load()
    assert library.system("worthiness").text == (PACKAGED / "worthiness.system.md").read_text()
    filled = library.system("grouping-assign", id_pattern="P", max_description=9).text
    assert "{id_pattern}" not in filled and "{max_description}" not in filled
    assert "{`kind`" in library.system("grouping-supervise").text


def test_the_correction_template_renders_what_the_engine_sends():
    problems = ["a", "b"]
    text = PromptLibrary.load().correction("rejection", problems="\n".join(f"  - {p}" for p in problems)).text
    assert text == rejection(problems)


def test_values_and_lifetimes_are_checked():
    library = PromptLibrary.load()
    with pytest.raises(PromptError, match="value_mismatch"):
        library.system("grouping-assign", id_pattern="P")
    with pytest.raises(PromptError, match="lifetime_mismatch"):
        library.system("rejection", problems="x")
    with pytest.raises(PromptError, match="prompt_unknown"):
        library.system("nope")


def test_an_override_replaces_by_file_name_and_rejects_strays(tmp_path):
    (tmp_path / "worthiness.system.md").write_text("mine")
    library = PromptLibrary.load(tmp_path)
    assert library.system("worthiness").text == "mine" and library.source("worthiness") == tmp_path / "worthiness.system.md"
    (tmp_path / "worthines.system.md").write_text("typo")
    with pytest.raises(PromptError, match="prompt_unknown"):
        PromptLibrary.load(tmp_path)


def test_an_override_must_keep_declared_placeholders(tmp_path):
    (tmp_path / "grouping-assign.system.md").write_text("no placeholders")
    with pytest.raises(PromptError, match="placeholder_missing"):
        PromptLibrary.load(tmp_path)


def test_the_fingerprint_moves_with_the_system_prompt_and_the_schema():
    a, b = SystemPrompt("s", "one"), SystemPrompt("s", "two")
    assert fingerprint(a, {"x": 1}) != fingerprint(b, {"x": 1}) != fingerprint(b, {"x": 2})
    assert fingerprint(a, {"x": 1, "y": 2}) == fingerprint(a, {"y": 2, "x": 1})
