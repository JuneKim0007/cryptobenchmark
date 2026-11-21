"""A path a settings file names: perfrepair.yaml's through paths.against (~/ expanded, joined, resolved); a global.yaml's test set where
Kotlin finds it (paths.beside: joined to the file's folder, nothing expanded or resolved)."""
from types import SimpleNamespace

import pytest

from perfrepair.config.load import Loaded
from perfrepair.device.delta_config import _test_set
from perfrepair.device.selection import relocated
from cryptobench.shared.settings import authored
from cryptobench.shared.errors.input_error import InputError

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


def test_a_home_value_of_a_test_set_stays_beside_the_base_in_relocated(tmp_path, home):
    base = tmp_path / "global.yaml"
    base.write_text("selection: {testSet: ~/t.yaml}\n")
    assert relocated(authored.read(base))["selection"]["testSet"] == str(tmp_path / "~" / HOME_FILE)


def test_a_home_value_of_a_test_set_is_not_expanded_in_the_delta_plan(tmp_path, home):
    (home / HOME_FILE).write_text("")
    given = authored.Authored(tmp_path / "global.yaml", {"selection": {"testSet": "~/t.yaml"}})
    with pytest.raises(InputError, match=r"^delta_unconfigured: .* names test set '~/t.yaml', not a file"):
        _test_set(tmp_path / "global.yaml", given)


def test_a_relative_test_set_stays_beside_its_config(tmp_path):
    (tmp_path / "t.yaml").write_text("")
    given = authored.Authored(tmp_path / "g.yaml", {"selection": {"testSet": "t.yaml"}})
    assert _test_set(tmp_path / "g.yaml", given) == tmp_path / "t.yaml"
