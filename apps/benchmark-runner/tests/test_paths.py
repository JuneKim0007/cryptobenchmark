"""The path interface: roots, locations, packaged data, settings values, the results tree."""
import pathlib
import sys

import pytest

from cryptobench import paths
from cryptobench.coded import InputError


def checkout(folder):
    (folder / "algorithms").mkdir(parents=True)
    pipeline = folder / paths.PIPELINE
    pipeline.parent.mkdir(parents=True)
    pipeline.write_text("")
    return folder


def test_code_root_finds_this_checkout():
    assert (paths.code_root() / paths.PIPELINE).is_file()


def test_code_root_prefers_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.CODE_ROOT_ENV, str(checkout(tmp_path / "other")))
    assert paths.code_root() == (tmp_path / "other").resolve()


def test_code_root_refuses_a_folder_that_is_no_checkout(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.CODE_ROOT_ENV, str(tmp_path))
    with pytest.raises(InputError) as refused:
        paths.code_root()
    assert refused.value.code == "root_not_found"


def test_code_root_follows_the_running_script_over_the_installed_library(tmp_path, monkeypatch):
    other = checkout(tmp_path / "other")
    script = other / "apps/benchmark-runner/pipeline.py"
    monkeypatch.delenv(paths.CODE_ROOT_ENV, raising=False)
    monkeypatch.setattr(sys.modules["__main__"], "__file__", str(script), raising=False)
    assert paths.code_root() == other.resolve()


def test_benchmark_root_order(tmp_path, monkeypatch):
    a, b = checkout(tmp_path / "a"), checkout(tmp_path / "b")
    monkeypatch.setenv(paths.BENCHMARK_ROOT_ENV, str(b))
    assert paths.benchmark_root() == b.resolve()
    assert paths.benchmark_root(a) == a.resolve()
    monkeypatch.delenv(paths.BENCHMARK_ROOT_ENV)
    assert paths.benchmark_root() == paths.code_root()


def test_benchmark_root_refuses_with_the_callers_error(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.BENCHMARK_ROOT_ENV, str(tmp_path))
    with pytest.raises(KeyError, match="CRYPTOBENCH_ROOT"):
        paths.benchmark_root(error=KeyError)


def test_repo_locations_exist():
    r = paths.repo()
    for location in (r.algorithms, r.config, r.default_global, r.runner, r.pipeline, r.dependencies, r.energy, r.gradle_root, r.gradlew,
                     r.benchmark_cli, r.engine_operations, r.preparation_resources, r.perf_repair, r.perf_repair_source, r.library):
        assert location.exists(), location


@pytest.mark.parametrize("value", ["sub/x.yaml", "/abs/x.yaml"])
def test_against_joins_to_the_settings_folder(tmp_path, value):
    assert paths.against(tmp_path / "settings.yaml", value) == (tmp_path / value).resolve()


def test_against_resolves_dotdot(tmp_path):
    assert paths.against(tmp_path / "s" / "settings.yaml", "../x.yaml") == (tmp_path / "x.yaml").resolve()


def test_against_expands_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert paths.against("/x/settings.yaml", "~/y.yaml") == (tmp_path / "y.yaml").resolve()


def test_in_temp():
    assert paths.in_temp("/tmp/x") and not paths.in_temp(paths.code_root())


def test_results_lists_finished_devices(tmp_path):
    (tmp_path / "done").mkdir()
    (tmp_path / "done" / paths.MANIFEST).write_text("")
    (tmp_path / "partial").mkdir()
    assert paths.Results(tmp_path).devices() == ["done"]
    assert paths.Results(tmp_path / "gone").devices() == []


def test_run_tree_names_each_section(tmp_path):
    tree = paths.Results(tmp_path).device("id")
    assert tree.root == tmp_path / "id" and tree.manifest == tmp_path / "id/manifest.yaml"
    assert tree.configuration.guide == tmp_path / "id/configuration/guide.yaml"
    assert tree.benchmark.process(2).json == tmp_path / "id/benchmark/process-2/benchmark.json"
    assert tree.check.preparation.prepared == tmp_path / "id/check/preparation/prepared.yaml"
    assert tree.log.ai("job") == tmp_path / "id/log/ai/job.yaml"
    assert tree.log.events == tmp_path / "id/log/events.jsonl"
    assert tree.app("demo").finished == tmp_path / "id/demo/finished.json"
    assert tree.grouping.groups == tmp_path / "id/grouping/groups.json"


def test_app_name_is_one_segment(tmp_path):
    with pytest.raises(ValueError):
        paths.RunTree(tmp_path).app("../up")


def test_device_dirs_change_at_sdk_29():
    assert str(paths.DeviceDirs(29).plan) == f"/sdcard/Android/media/{paths.device_dirs.PACKAGE}/{paths.device_dirs.PLAN_DIRECTORY}"
    assert str(paths.DeviceDirs(28).output).endswith("/cache")


def test_contract_names_are_unique_kotlin_constants():
    assert len(set(paths.CONTRACT.values())) == len(paths.CONTRACT)
