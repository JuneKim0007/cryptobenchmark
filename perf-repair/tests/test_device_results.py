import argparse
import json
from pathlib import Path

import pytest

from perfrepair.app.path_id import app_id, path_id, unit_id
from perfrepair.config.args import add_config_arg
from perfrepair.config.device_results import _warn_if_temp, add_device_results_arg, fill_device_results, select_device
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.inputs.resolve import InputError
from perfrepair.run_dir import app_dirs, device_folders


def device(root, name):
    (root / name).mkdir(parents=True)
    (root / name / "manifest.yaml").write_text("schemaVersion: 1\n")
    return root / name


def filled(tmp_path, settings, flag=None):
    config = tmp_path / "c.yaml"
    config.write_text(settings)
    parser = argparse.ArgumentParser()
    add_device_results_arg(parser)
    add_config_arg(parser)
    args = parser.parse_args(["--perfrepair-config", str(config), *(["--device-results", str(flag)] if flag else [])])
    fill_device_results(parser, args)
    return args.device_results


def test_only_a_folder_with_a_manifest_is_a_device(tmp_path):
    device(tmp_path, "a")
    (tmp_path / "failed" / "discovery").mkdir(parents=True)
    (tmp_path / ".staging-x" / "discovery").mkdir(parents=True)
    (tmp_path / "pipeline.log").write_text("")
    assert device_folders(tmp_path) == ["a"]


def test_the_only_device_is_used_without_a_setting(tmp_path):
    only = device(tmp_path, "a")
    assert select_device(tmp_path, None) == only


def test_several_devices_are_one_coded_line_listing_them(tmp_path):
    device(tmp_path, "a")
    device(tmp_path, "b")
    with pytest.raises(ValueError, match=r"^several_device_results: .* holds a, b; set device.id or pass --device-results$"):
        select_device(tmp_path, None)


def test_device_id_selects_and_an_absent_one_never_falls_back(tmp_path):
    device(tmp_path, "a")
    wanted = device(tmp_path, "b")
    assert select_device(tmp_path, "b") == wanted
    with pytest.raises(ValueError, match=r"^device_not_in_results: c; "):
        select_device(tmp_path, "c")


def test_an_empty_root_says_to_run_the_benchmark(tmp_path):
    with pytest.raises(ValueError, match=r"^no_device_results: "):
        select_device(tmp_path, None)


def test_the_settings_reach_the_folder(tmp_path):
    device(tmp_path / "results", "a")
    wanted = device(tmp_path / "results", "b")
    assert filled(tmp_path, "paths: {results: results}\ndevice: {id: b}\n") == wanted


def test_the_flag_outranks_the_settings(tmp_path):
    assert filled(tmp_path, "paths: {results: results}\ndevice: {id: b}\n", tmp_path / "mine") == tmp_path / "mine"


def test_a_bad_device_id_stops_instead_of_using_the_only_device(tmp_path):
    device(tmp_path / "results", "a")
    with pytest.raises(InputError, match=r"^invalid: device.id 3, "):
        filled(tmp_path, "paths: {results: results}\ndevice: {id: 3}\n")


def test_a_root_given_as_the_device_folder_is_one_coded_line(tmp_path):
    device(tmp_path / "results", "a")
    with pytest.raises(ValueError, match=r"^not_device_results: .*results has no manifest.yaml; pass <root>/<device id>$"):
        filled(tmp_path, "", tmp_path / "results")


def test_a_command_reading_a_missing_manifest_is_one_coded_line(tmp_path, capsys):
    assert grouping(["build", "--device-results", str(tmp_path)]) == 1
    assert capsys.readouterr().err.splitlines()[-1] == \
        f"error not_device_results: {tmp_path} has no manifest.yaml; pass <root>/<device id>"


def test_a_command_reports_several_devices_as_its_error_line(tmp_path, capsys):
    device(tmp_path / "results", "a")
    device(tmp_path / "results", "b")
    config = tmp_path / "c.yaml"
    config.write_text("paths: {results: results}\n")
    assert grouping(["report", "--perfrepair-config", str(config)]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error several_device_results: ")


def test_a_temporary_folder_warns_once_and_another_does_not(tmp_path, caplog):
    _warn_if_temp(tmp_path)
    _warn_if_temp(tmp_path)
    _warn_if_temp(Path.home() / "capstone" / "runs" / "x")
    [message] = caplog.messages
    assert message.startswith(f"results_in_temp: {tmp_path} ")


def test_the_path_id_is_slug_safe_and_follows_the_absolute_path(tmp_path):
    (tmp_path / "my app!").mkdir()
    (tmp_path / "other" / "my app!").mkdir(parents=True)
    made = path_id(tmp_path / "my app!")
    assert made.startswith("my-app-") and len(made.rsplit("-", 1)[1]) == 8
    assert made == path_id(tmp_path / "other" / ".." / "my app!")
    assert made != path_id(tmp_path / "other" / "my app!")
    assert path_id("/").startswith("app-")


def test_a_project_root_finds_its_unit_of_a_multi_root_folder(tmp_path):
    mono, folder = tmp_path / "mono", tmp_path / "device" / unit_id(path_id(tmp_path / "mono"), "sub/android")
    folder.mkdir(parents=True)
    (folder / "app.json").write_text(json.dumps({"root": str((mono / "sub/android").resolve())}))
    (tmp_path / "device" / "grouping").mkdir()
    assert folder.name.endswith(".sub.android") and app_dirs(tmp_path / "device") == [folder]
    assert app_id(tmp_path / "device", mono / "sub/android") == folder.name
    assert app_id(tmp_path / "device", tmp_path / "elsewhere") == path_id(tmp_path / "elsewhere")


def test_validation_reports_several_devices_as_its_error_line(tmp_path, capsys):
    from perfrepair.validation.__main__ import main as validation
    device(tmp_path / "results", "a")
    device(tmp_path / "results", "b")
    config = tmp_path / "c.yaml"
    config.write_text("paths: {results: results}\n")
    assert validation(["--perfrepair-config", str(config)]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error several_device_results: ")
