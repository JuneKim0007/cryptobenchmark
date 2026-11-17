"""An energy source's venv: built once per requirements digest, nothing left after a failed install."""
import pathlib
import subprocess

import pytest

from cryptobench.stages.measurement.energy import install


def fake_run(failing_step=None):
    calls = []

    def run(step, **_):
        calls.append(step)
        if step[1:3] == ["-m", "venv"]:
            (pathlib.Path(step[3]) / "bin").mkdir(parents=True)
        code = 1 if failing_step is not None and len(calls) - 1 == failing_step else 0
        return subprocess.CompletedProcess(step, code, "", "ERROR: No matching distribution found for manafa==0.4.14" if code else "")
    return run, calls


@pytest.fixture(autouse=True)
def cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))


def test_the_first_use_builds_the_venv_with_every_requirements_file_and_the_second_reuses_it():
    run, calls = fake_run()
    python = install.installed("manafa", run)
    assert python.endswith("/bin/python") and "/cryptobench/energy/manafa-" in python
    assert [a for a in calls[1] if a.endswith(".txt")] == [str(f) for f in install.files("manafa")]
    assert install.installed("manafa", run) == python and len(calls) == 2


def test_a_failed_install_leaves_nothing_behind_and_says_why():
    run, _ = fake_run(failing_step=1)
    with pytest.raises(install.InstallFailed, match="energy_install_failed: manafa: ERROR: No matching distribution"):
        install.installed("manafa", run)
    assert not any(install.cache_root().iterdir())


def test_a_changed_requirements_file_means_a_new_venv(monkeypatch, tmp_path):
    first = install.venv("manafa")
    changed = tmp_path / "requirements-manafa.txt"
    changed.write_text("manafa==9.9\n")
    monkeypatch.setattr(install, "files", lambda _name: [changed])
    assert install.venv("manafa") != first
