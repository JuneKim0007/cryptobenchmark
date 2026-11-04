"""The facade's check over a tree of files; the parse-only JVM step is stubbed except in the tests that name it real."""
import pathlib
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from facade import check as check_module
from facade.check import check
from facade.tree import OVERRIDDEN, PACKAGED, direction_problems
from repo import ROOT
from stages import config_check

APP_MANIFEST = '<manifest package="demo"><application /></manifest>'


@pytest.fixture
def tree(tmp_path, monkeypatch):
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\n")
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    app = tmp_path / "app"
    (app / "src/main").mkdir(parents=True)
    (app / "build.gradle").write_text("apply plugin: 'com.android.application'\n")
    (app / "src/main/AndroidManifest.xml").write_text(APP_MANIFEST)
    (tmp_path / "p.yaml").write_text(yaml.safe_dump({"apps": {"targets": [str(app)]}}))
    (tmp_path / "s.yaml").write_text("schemaVersion: 1\nresults: r\ncrypto: {config: global.yaml}\nllm: {config: p.yaml}\n")
    monkeypatch.setattr(check_module, "parse_all", lambda files: [
        {"global": str(f), "testSet": str(f.parent / yaml.safe_load(f.read_text()).get("selection", {}).get("testSet", "set.yaml")), "bundled": []} for f in files])
    return tmp_path


def test_a_good_tree_has_no_problem_and_lists_every_catalog(tree):
    checked = check(tree / "s.yaml")
    assert checked.problems == []
    keys = [n.key for n in checked.nodes if n.kind != "catalog"]
    assert keys == ["settings", "results", "crypto.config", "selection.testSet", "llm.config", "apps.targets[0]"]
    catalogs = [n for n in checked.nodes if n.kind == "catalog"]
    assert {n.status for n in catalogs} == {PACKAGED} and any(n.path.name == "screening.yaml" for n in catalogs)
    assert any(n.path.name == "setup-catalog.yaml" for n in catalogs) and all(n.digest for n in catalogs)


def test_a_missing_path_is_named_with_the_key_and_the_file_holding_it(tree):
    (tree / "global.yaml").unlink()
    [problem] = check(tree / "s.yaml").problems
    assert problem == f"missing_file: {tree / 'global.yaml'} (crypto.config in {tree / 's.yaml'})"


def test_results_may_be_absent_but_its_parent_may_not(tree):
    (tree / "s.yaml").write_text("schemaVersion: 1\nresults: no/such/r\ncrypto: {config: global.yaml}\nllm: {config: p.yaml}\n")
    [problem] = check(tree / "s.yaml").problems
    assert problem.startswith("missing_file: ") and "the folder of results" in problem


@pytest.mark.parametrize("key, text, place", [
    ("paths.results", "paths: {results: there}\n", "results in the settings index"),
    ("device.benchmark.config", "device: {benchmark: {config: g.yaml}}\n", "crypto.config in the settings index"),
    ("apps.benchmarkConfig", "apps: {benchmarkConfig: g.yaml}\n", "crypto.harnessConfig in the settings index"),
    ("run.id", "run: {id: one}\n", "run.id in the settings index"),
    ("run.onExisting", "run: {onExisting: resume}\n", "run.onExisting in the settings index"),
])
def test_a_moved_key_is_a_placement_error_naming_the_new_place(tree, key, text, place):
    (tree / "p.yaml").write_text(text)
    [problem] = check(tree / "s.yaml").problems
    assert problem.startswith(f"placement: {key} is no perfrepair.yaml key; set {place}")


@pytest.mark.parametrize("text, line", [
    ("selection: {testSet: x}\n", "placement: selection in {f} belongs in the global.yaml"),
    ("crypto: {config: x}\n", "placement: crypto in {f} belongs in the settings index"),
    ("apps: {names: []}\n", "unknown_key: apps.names in {f}"),
])
def test_a_key_in_the_wrong_file_is_refused(tree, text, line):
    (tree / "p.yaml").write_text(text)
    problems = check(tree / "s.yaml").problems
    assert any(p.startswith(line.format(f=tree / "p.yaml")) for p in problems), problems


def test_no_targets_is_a_problem_before_any_phase(tree):
    (tree / "p.yaml").write_text("{}\n")
    assert check(tree / "s.yaml").problems[0].startswith("no_targets: apps.targets is unset")


def test_a_screening_override_is_listed_overridden_in_place_of_the_packaged_one(tree):
    from perfrepair.catalog.screening import SCREENING
    config = yaml.safe_load((tree / "p.yaml").read_text())
    (tree / "own.yaml").write_text(SCREENING.read_text())
    config["device"] = {"screening": {"catalog": "own.yaml"}}
    (tree / "p.yaml").write_text(yaml.safe_dump(config))
    checked = check(tree / "s.yaml")
    assert checked.problems == []
    catalogs = {n.path: n.status for n in checked.nodes if n.kind == "catalog"}
    assert catalogs[tree / "own.yaml"] == OVERRIDDEN and SCREENING not in catalogs


def test_a_bad_screening_override_is_caught_by_its_parser(tree):
    config = yaml.safe_load((tree / "p.yaml").read_text())
    (tree / "own.yaml").write_text("schemaVersion: 99\n")
    config["device"] = {"screening": {"catalog": "own.yaml"}}
    (tree / "p.yaml").write_text(yaml.safe_dump(config))
    assert check(tree / "s.yaml").problems[0].startswith("invalid: device.screening.catalog")


def test_the_llm_side_pointing_at_a_crypto_file_is_sideways(tree):
    config = yaml.safe_load((tree / "p.yaml").read_text())
    config["device"] = {"screening": {"catalog": "global.yaml"}}
    (tree / "p.yaml").write_text(yaml.safe_dump(config))
    problems = check(tree / "s.yaml").problems
    assert any(p.startswith("direction: ") and "sideways" in p for p in problems), problems


def test_a_test_set_pointing_back_at_its_config_is_upward(tree):
    (tree / "global.yaml").write_text("schemaVersion: 1\nselection: {testSet: global.yaml}\n")
    problems = check(tree / "s.yaml").problems
    assert any(p.startswith("direction: ") and "points up" in p for p in problems), problems


def test_a_targets_file_pointing_at_the_index_is_upward(tree):
    config = yaml.safe_load((tree / "p.yaml").read_text())
    config["apps"]["targets"] = "s.yaml"
    (tree / "p.yaml").write_text(yaml.safe_dump(config))
    problems = check(tree / "s.yaml").problems
    assert any(p.startswith("direction: ") and "points up" in p for p in problems), problems


def test_both_sides_naming_one_file_is_sideways(tree):
    (tree / "s.yaml").write_text("schemaVersion: 1\nresults: r\ncrypto: {config: p.yaml}\nllm: {config: p.yaml}\n")
    assert any("sideways" in p for p in direction_problems(check(tree / "s.yaml").nodes))


def test_the_real_parser_catches_a_typo_and_a_bad_provider_before_any_build(tmp_path):
    good = tmp_path / "global.yaml"
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: [{artifact: 'a:b:1', create: org.example.C}]}\n")
    [one] = config_check.parse_all([good])
    assert one["testSet"].endswith("set.yaml") and one["bundled"] == [{"artifact": "a:b:1", "create": "org.example.C"}]
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nrnu: {seed: 1}\n")
    with pytest.raises(config_check.ConfigCheckError, match="unknown_section"):
        config_check.parse_all([good])
    good.write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nproviders: {bundled: [{artifact: 'a:b:1', create: C}]}\n")
    with pytest.raises(config_check.ConfigCheckError, match="invalid_create"):
        config_check.parse_all([good])


def test_pipeline_refuses_a_typo_with_one_line_before_any_build(tmp_path):
    (tmp_path / "set.yaml").write_text("schemaVersion: 1\n")
    (tmp_path / "global.yaml").write_text("schemaVersion: 1\nselection: {testSet: set.yaml}\nrnu: {seed: 1}\n")
    done = subprocess.run([sys.executable, str(ROOT / "scripts/pipeline.py"), "--config", str(tmp_path / "global.yaml"), "--device",
                           "--results", str(tmp_path / "r")], capture_output=True, text=True, check=False)
    assert done.returncode == 1 and done.stderr.strip().startswith("error: global.yaml: unknown_section")
    assert "\n" not in done.stderr.strip() and not (tmp_path / "r").exists()


def test_a_lookup_cannot_decide_the_check(tree, monkeypatch):
    monkeypatch.setenv("CRYPTOBENCH_CONFIG", str(tree / "no-such-global.yaml"))
    monkeypatch.setenv("PERFREPAIR_CONFIG", str(tree / "no-such-perfrepair.yaml"))
    monkeypatch.setenv("HOME", str(tree / "no-home"))
    checked = check(tree / "s.yaml")
    assert checked.problems == []
    assert {n.key: n.path for n in checked.nodes}["llm.config"] == tree / "p.yaml"
