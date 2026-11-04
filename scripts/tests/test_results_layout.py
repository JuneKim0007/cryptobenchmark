import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pipeline  # noqa: E402
from failure import fail  # noqa: E402
from results import layout, select  # noqa: E402
from device.identity import device_id  # noqa: E402

RUNTIME = {"model": "probed", "sdkInt": 36, "fingerprint": "a/b/c:16/X/1:user/release-keys"}


def write(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def stage_with(root):
    stage = root / ".staging-test"
    write(stage / "discovery/probe_new.yaml")
    write(stage / "configuration/effective.yaml", "new")
    return stage


def test_a_failed_run_leaves_no_stage(tmp_path):
    with pytest.raises(SystemExit):
        with layout.staged(tmp_path) as stage:
            write(stage / "discovery/probe.yaml")
            fail("boom")
    assert list(tmp_path.iterdir()) == []


def test_overwrite_replaces_discovery_and_drops_the_old_manifest_but_nothing_of_perf_repair(tmp_path):
    target = tmp_path / "device"
    write(target / "discovery/probe_old.yaml")
    write(target / layout.MANIFEST)
    write(target / "grouping/groups.json")
    layout.publish(stage_with(tmp_path), target, "overwrite")
    assert [p.name for p in (target / "discovery").iterdir()] == ["probe_new.yaml"]
    assert (target / "configuration/effective.yaml").read_text() == "new"
    assert not (target / layout.MANIFEST).exists() and (target / "grouping/groups.json").is_file()


@pytest.mark.parametrize("mode", ["keep", "reuse"])
def test_keep_and_reuse_add_to_the_discovery_already_there(tmp_path, mode):
    target = tmp_path / "device"
    write(target / "discovery/probe_old.yaml")
    layout.publish(stage_with(tmp_path), target, mode)
    assert sorted(p.name for p in (target / "discovery").iterdir()) == ["probe_new.yaml", "probe_old.yaml"]


def test_interop_beside_a_finished_run_keeps_its_configuration_and_adds_to_its_manifest(tmp_path):
    target = tmp_path / "device"
    probe = write(target / "discovery/probe_old.yaml", yaml.safe_dump({"runtime": RUNTIME}))
    write(target / "configuration/effective.yaml", "old")
    stage = stage_with(tmp_path)
    write(stage / "interop/interop.yaml")
    (target / "g.yaml").write_text("schemaVersion: 1\n")
    pipeline.manifest(target, "host", target / "g.yaml", {"probe": probe})
    layout.publish_interop(stage, target)
    pipeline.add_to_manifest(target, {"interop": target / "interop/interop.yaml"})
    assert (target / "configuration/effective.yaml").read_text() == "old"
    assert (target / "discovery/probe_new.yaml").is_file()
    files = yaml.safe_load((target / layout.MANIFEST).read_text())["files"]
    assert files == {"probe": "discovery/probe_old.yaml", "interop": "interop/interop.yaml"}


def test_only_a_folder_with_a_manifest_is_a_device(tmp_path):
    write(tmp_path / "a/manifest.yaml")
    write(tmp_path / "failed/discovery/probe.yaml")
    write(tmp_path / ".staging-x/discovery/probe.yaml")
    assert select.device_folders(tmp_path) == ["a"]
    assert select.device_folder(tmp_path) == tmp_path / "a"


@pytest.mark.parametrize("wanted, code", [(None, "several_device_results: "), ("c", "device_not_in_results: c")])
def test_selection_is_one_coded_line(tmp_path, capsys, wanted, code):
    write(tmp_path / "a/manifest.yaml")
    write(tmp_path / "b/manifest.yaml")
    with pytest.raises(SystemExit):
        select.device_folder(tmp_path, wanted)
    message = capsys.readouterr().err
    assert message.startswith(f"error: {code}") and message.count("\n") == 1


def test_a_root_with_no_finished_run_says_so(tmp_path, capsys):
    with pytest.raises(SystemExit):
        select.device_folder(tmp_path)
    assert "no_device_results" in capsys.readouterr().err


def test_a_temporary_root_warns_and_any_other_does_not(tmp_path, capsys):
    layout.warn_if_temp(tmp_path)
    assert capsys.readouterr().out.startswith("warning: results_in_temp: ")
    layout.warn_if_temp(pathlib.Path.home() / "capstone/runs/x")
    assert capsys.readouterr().out == ""


def harness_in(folder, device):
    harness = write(folder / "app-00000000/harness.yaml")
    write(folder / layout.MANIFEST, yaml.safe_dump({"deviceId": device}))
    return harness


def test_a_harness_measured_on_its_own_device_passes(tmp_path):
    capture = write(tmp_path / "probe.yaml", yaml.safe_dump({"runtime": RUNTIME}))
    pipeline.require_harness_device(harness_in(tmp_path / "d", device_id(RUNTIME)), capture)


def test_a_harness_measured_on_another_device_stops(tmp_path, capsys):
    capture = write(tmp_path / "probe.yaml", yaml.safe_dump({"runtime": RUNTIME}))
    with pytest.raises(SystemExit):
        pipeline.require_harness_device(harness_in(tmp_path / "d", "other-api1-00000000"), capture)
    assert "harness_other_device" in capsys.readouterr().err


def test_a_harness_run_takes_no_results_root(capsys):
    options = type("Options", (), {"results": "r", "harness": "h.yaml"})
    with pytest.raises(SystemExit):
        pipeline.measured_folder(options)
    assert "a --harness run writes measured/ beside its harness.yaml" in capsys.readouterr().err


def test_a_write_that_fails_midway_leaves_the_old_manifest_whole_and_no_temporary(tmp_path, monkeypatch):
    path = write(tmp_path / layout.MANIFEST, "old: whole\n")

    def broken(_descriptor):
        raise OSError("disk full")
    monkeypatch.setattr(layout.os, "fsync", broken)
    with pytest.raises(OSError):
        layout.write_atomic(path, "new: half\n")
    assert path.read_text() == "old: whole\n" and [p.name for p in tmp_path.iterdir()] == [layout.MANIFEST]
    monkeypatch.undo()
    layout.write_atomic(path, "new: whole\n")
    assert path.read_text() == "new: whole\n"


def test_a_failed_run_leaves_the_last_finished_folder_and_a_finished_one_replaces_it(tmp_path):
    folder = tmp_path / "scoped"
    folder.mkdir()
    (folder / "benchmark.json").write_text("old")
    with pytest.raises(SystemExit):
        with layout.kept_until_replaced(folder):
            folder.mkdir()
            (folder / "partial").write_text("half")
            raise SystemExit(1)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["scoped"] and (folder / "benchmark.json").read_text() == "old"
    with layout.kept_until_replaced(folder):
        folder.mkdir()
        (folder / "benchmark.json").write_text("new")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["scoped"] and (folder / "benchmark.json").read_text() == "new"


def test_a_folder_set_aside_by_a_killed_run_comes_back_first(tmp_path):
    (tmp_path / "scoped.previous").mkdir()
    (tmp_path / "scoped.previous" / "benchmark.json").write_text("old")
    (tmp_path / "scoped").mkdir()
    with pytest.raises(RuntimeError):
        with layout.kept_until_replaced(tmp_path / "scoped"):
            raise RuntimeError("halted")
    assert (tmp_path / "scoped" / "benchmark.json").read_text() == "old" and not (tmp_path / "scoped.previous").exists()
