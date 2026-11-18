"""Characterization (Py-P7), changed: a device run locks its phone by serial, whatever its results root; a second run on that phone is refused
device_busy before it writes anything; the results-root lock nests inside. A blank serial gets an unstable_id notice and no phone lock. Before,
the only lock was the results root's, so two roots on one serial both ran."""
import os, pathlib, subprocess, sys, types

import pytest

from cryptobench.shared import paths
from cryptobench.shared.device.adb import Device
from cryptobench.shared.errors.input_error import InputError
from test_rerun_safety import Rerun

SERIAL = "56301AAAA00001"
HOLD = ("import sys; from cryptobench.shared import paths; from cryptobench.shared.results.lock import DeviceLock; "
        "DeviceLock.take_key(paths.phone_lock(sys.argv[1]), sys.argv[1]); print('held', flush=True); sys.stdin.read()")


def holding(serial):
    library = pathlib.Path(paths.__file__).parents[3]
    holder = subprocess.Popen([sys.executable, "-c", HOLD, serial], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              env={**os.environ, "PYTHONPATH": str(library)})
    assert holder.stdout.readline().strip() == "held"
    return holder


def test_a_second_run_on_one_phone_is_device_busy_on_any_results_root(tmp_path, monkeypatch):
    monkeypatch.setenv("ANDROID_SERIAL", SERIAL)
    holder = holding(SERIAL)
    rerun = Rerun(tmp_path, monkeypatch)
    rerun.root = tmp_path / "second"
    try:
        with pytest.raises(InputError, match=rf"^device_busy: phone {SERIAL} is in use by another run \(pid {holder.pid}\)"):
            rerun()
        assert not rerun.root.exists()
    finally:
        holder.stdin.close()
        holder.wait(10)
    rerun()
    assert paths.finished(rerun.device)


def test_another_phone_runs_while_one_is_held(tmp_path, monkeypatch):
    holder = holding(SERIAL)
    try:
        monkeypatch.setenv("ANDROID_SERIAL", "56301BBBB00002")
        rerun = Rerun(tmp_path, monkeypatch)
        rerun()
        assert paths.finished(rerun.device)
    finally:
        holder.stdin.close()
        holder.wait(10)


def test_a_blank_serial_runs_unlocked_with_an_unstable_id_notice(tmp_path, monkeypatch, capsys):
    rerun = Rerun(tmp_path, monkeypatch)
    rerun.phone.serial = lambda: ""
    rerun()
    assert paths.finished(rerun.device) and not (paths.user_cache() / "locks").exists()
    assert "unstable_id: adb reports no serial for this device" in capsys.readouterr().out


@pytest.mark.parametrize("named, answer, serial", [(SERIAL, "other", SERIAL), (None, f"{SERIAL}\n", SERIAL), (None, "unknown\n", ""), (None, "", "")])
def test_a_device_serial_is_android_serial_else_adb_get_serialno(monkeypatch, named, answer, serial):
    if named:
        monkeypatch.setenv("ANDROID_SERIAL", named)
    else:
        monkeypatch.delenv("ANDROID_SERIAL", raising=False)
    device = Device(pathlib.Path("."), False, False)
    monkeypatch.setattr(device, "run", lambda *arguments, **_: types.SimpleNamespace(stdout=answer) if arguments == ("get-serialno",) else None)
    assert device.serial() == serial
