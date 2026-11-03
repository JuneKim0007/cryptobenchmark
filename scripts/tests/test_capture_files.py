import pathlib, sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import capture_files  # noqa: E402
import pipeline  # noqa: E402


def write(directory, stamp, trial=True):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"probe_{stamp}.yaml").write_text("x")
    (directory / f"probe_classes_{stamp}.yaml").write_text("x")
    if trial:
        (directory / f"trial_{stamp}.yaml").write_text("x")


def test_a_device_whose_clock_is_behind_still_gets_the_capture_it_just_wrote(tmp_path):
    write(tmp_path, "20270101T000000Z")
    before = capture_files.stamped(tmp_path)
    write(tmp_path, "20260301T000000Z")
    assert capture_files.added(tmp_path, before) == (tmp_path / "probe_20260301T000000Z.yaml", tmp_path / "trial_20260301T000000Z.yaml")


def test_the_trial_is_the_one_with_the_captures_stamp_never_another(tmp_path):
    write(tmp_path, "20270101T000000Z")
    write(tmp_path, "20260301T000000Z", trial=False)
    with pytest.raises(SystemExit):
        capture_files.pair(tmp_path / "probe_20260301T000000Z.yaml")


def test_a_probe_that_added_no_capture_or_two_stops(tmp_path, capsys):
    write(tmp_path, "20260301T000000Z")
    with pytest.raises(SystemExit):
        capture_files.added(tmp_path, capture_files.stamped(tmp_path))
    assert "added 0 captures" in capsys.readouterr().err


def test_the_host_capture_is_the_one_probekt_printed(tmp_path):
    write(tmp_path, "20270101T000000Z")
    write(tmp_path, "20260301T000000Z")
    lines = [str(tmp_path / "probe_20260301T000000Z.yaml"), str(tmp_path / "probe_classes_20260301T000000Z.yaml"),
             str(tmp_path / "trial_20260301T000000Z.yaml"), "/c/inventory.yaml"]
    assert capture_files.printed(lines, tmp_path)[0].name == "probe_20260301T000000Z.yaml"


def test_after_a_publish_into_a_kept_discovery_the_run_reads_its_own_capture(tmp_path):
    write(tmp_path / "discovery", "20270101T000000Z")
    write(tmp_path / "discovery", "20260301T000000Z")
    _, _, capture, trial, files = pipeline.located(tmp_path, "probe_20260301T000000Z.yaml")
    assert (capture.name, trial.name) == ("probe_20260301T000000Z.yaml", "trial_20260301T000000Z.yaml")
    assert files["probe"] == capture
