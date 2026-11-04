import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import global_file  # noqa: E402


def test_a_named_config_that_is_missing_is_refused_by_where_it_was_named(tmp_path, monkeypatch, capsys):
    absent = tmp_path / "absent.yaml"
    monkeypatch.setenv("CRYPTOBENCH_CONFIG", str(absent))
    with pytest.raises(SystemExit):
        global_file.global_config(None)
    assert f"missing_file: {absent} (CRYPTOBENCH_CONFIG)" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        global_file.global_config(str(absent))
    assert f"missing_file: {absent} (--config)" in capsys.readouterr().err


def test_the_argument_comes_before_the_environment_which_comes_before_the_defaults(tmp_path, monkeypatch):
    named, other = tmp_path / "named.yaml", tmp_path / "other.yaml"
    named.write_text(""), other.write_text("")
    monkeypatch.setenv("CRYPTOBENCH_CONFIG", str(named))
    assert global_file.global_config(None) == named.resolve()
    assert global_file.global_config(str(other)) == other.resolve()
    monkeypatch.delenv("CRYPTOBENCH_CONFIG")
    monkeypatch.setattr(global_file.pathlib.Path, "home", lambda: tmp_path / "home")
    monkeypatch.setattr(global_file, "ROOT", tmp_path / "repo")
    with pytest.raises(SystemExit):
        global_file.global_config(None)
