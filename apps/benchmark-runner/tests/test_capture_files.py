
import pytest

from stages import capture_files  # noqa: E402
from stages import discover  # noqa: E402


def write(directory, stamp, trial=True):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"probe_{stamp}.yaml").write_text("x")
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
    with pytest.raises(SystemExit) as stopped:
        capture_files.pair(tmp_path / "probe_20260301T000000Z.yaml")
    assert stopped.value.code == 1


def test_a_probe_that_added_no_capture_stops(tmp_path):
    write(tmp_path, "20260301T000000Z")
    with pytest.raises(SystemExit) as stopped:
        capture_files.added(tmp_path, capture_files.stamped(tmp_path))
    assert stopped.value.code == 1


def test_the_host_capture_is_the_one_probekt_printed(tmp_path):
    write(tmp_path, "20270101T000000Z")
    write(tmp_path, "20260301T000000Z")
    lines = [str(tmp_path / "probe_20260301T000000Z.yaml"), str(tmp_path / "trial_20260301T000000Z.yaml"), "/c/inventory.yaml"]
    assert capture_files.printed(lines, tmp_path)[0].name == "probe_20260301T000000Z.yaml"


def test_after_a_publish_into_a_kept_discovery_the_run_reads_its_own_capture(tmp_path):
    write(tmp_path / "discovery", "20270101T000000Z")
    write(tmp_path / "discovery", "20260301T000000Z")
    _, _, capture, trial, files = discover.located(tmp_path, "probe_20260301T000000Z.yaml")
    assert (capture.name, trial.name) == ("probe_20260301T000000Z.yaml", "trial_20260301T000000Z.yaml")
    assert files["probe"] == capture


def test_reuse_that_probed_again_says_so_and_a_reused_capture_is_silent(tmp_path, capsys):
    write(tmp_path, "20260101T000000Z")
    before = capture_files.stamped(tmp_path)
    capture_files.reprobed(before, tmp_path / "probe_20260101T000000Z.yaml")
    assert capsys.readouterr().out == ""
    capture_files.reprobed(before, tmp_path / "probe_20260102T000000Z.yaml")
    assert "discovery_reprobed" in capsys.readouterr().out
