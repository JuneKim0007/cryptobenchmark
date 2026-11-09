"""A path a settings file names: one rule everywhere, listed in the change that made it one (~/ expanded, joined to the file's folder, resolved)."""
from types import SimpleNamespace

import pytest

from perfrepair.config.load import Loaded
from perfrepair.device.delta_config import _test_set
from perfrepair.device.selection import relocated

HOME_FILE = "t.yaml"


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def test_a_setting_with_dotdot_is_the_real_folder(tmp_path):
    (tmp_path / "s").mkdir()
    loaded = SimpleNamespace(settings={"k": "../x.yaml"}, file=tmp_path / "s/perfrepair.yaml")
    assert Loaded._file_value(loaded, SimpleNamespace(key="k", path=True)) == (tmp_path / "x.yaml").resolve()


def test_a_home_value_of_a_test_set_is_expanded_in_relocated(tmp_path, home):
    base = tmp_path / "global.yaml"
    base.write_text("selection: {testSet: ~/t.yaml}\n")
    assert relocated(base)["selection"]["testSet"] == str((home / HOME_FILE).resolve())


def test_a_home_value_of_a_test_set_is_expanded_in_the_delta_plan(tmp_path, home):
    (home / HOME_FILE).write_text("")
    assert _test_set(tmp_path / "global.yaml", {"selection": {"testSet": "~/t.yaml"}}) == (home / HOME_FILE).resolve()


def test_a_relative_test_set_stays_beside_its_config(tmp_path):
    (tmp_path / "t.yaml").write_text("")
    assert _test_set(tmp_path / "g.yaml", {"selection": {"testSet": "t.yaml"}}) == (tmp_path / "t.yaml").resolve()
