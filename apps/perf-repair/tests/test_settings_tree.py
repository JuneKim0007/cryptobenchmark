"""The facade's read of perfrepair.yaml: real parsers, its pointers, unknown keys refused, every file-valued row covered."""
import yaml
from perfrepair.guide.settings_tree import PARSERS, llm_tree, packaged_catalogs
from perfrepair.inputs.table import ROWS, Row

APP = "tests/fixtures/app"


def tree(tmp_path, document):
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(document))
    return llm_tree(path)


def test_every_file_valued_row_has_its_parser():
    assert {r.key for r in ROWS if isinstance(r, Row) and r.path} == set(PARSERS)


def test_the_targets_file_and_its_entries_are_pointers(tmp_path):
    (tmp_path / "t.yaml").write_text(yaml.safe_dump([{"path": "a"}]))
    read = tree(tmp_path, {"apps": {"targets": "t.yaml"}})
    assert [(p.key, p.path, p.kind) for p in read.pointers] == [("apps.targets", tmp_path / "t.yaml", "targets"),
                                                                ("apps.targets[0]", tmp_path / "a", "target")]
    assert read.problems[0].startswith("no_targets: apps.targets in ")


def test_an_error_row_with_a_bad_value_is_a_problem(tmp_path):
    read = tree(tmp_path, {"device": {"id": 3}, "apps": {"targets": ["x"]}})
    assert any(p.startswith("invalid: device.id 3") for p in read.problems)


def test_a_prompts_folder_with_a_stray_file_is_caught_by_its_parser(tmp_path):
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "stray.md").write_text("x")
    read = tree(tmp_path, {"paths": {"prompts": "prompts"}, "apps": {"targets": ["x"]}})
    assert any(p.startswith("invalid: paths.prompts") and "prompt_unknown" in p for p in read.problems)


def test_a_moved_key_is_the_one_problem(tmp_path):
    read = tree(tmp_path, {"run": {"id": "one"}})
    assert len(read.problems) == 1 and read.problems[0].startswith("placement: run.id")


def test_the_packaged_catalogs_are_listed_from_the_package():
    assert {p.name for p in packaged_catalogs()} >= {"screening.yaml", "criteria.yaml", "prompts.yaml"}
