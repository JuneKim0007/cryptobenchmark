"""Characterization (Py-P7): the run lock is keyed by the results root, not the phone: while another process holds one root for a serial, a run
on a second root with the same ANDROID_SERIAL measures."""
import os, pathlib, subprocess, sys

from cryptobench.shared import paths
from cryptobench.shared.device.adb import Device
from test_rerun_safety import HOLD, Rerun

SERIAL = "56301AAAA00001"


def test_today_two_results_roots_on_one_serial_both_run(tmp_path, monkeypatch):
    monkeypatch.setenv("ANDROID_SERIAL", SERIAL)
    first = tmp_path / "first"
    first.mkdir()
    library = pathlib.Path(paths.__file__).parents[3]
    holder = subprocess.Popen([sys.executable, "-c", HOLD, str(first)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                              env={**os.environ, "PYTHONPATH": str(library)})
    try:
        assert holder.stdout.readline().strip() == "held"
        rerun = Rerun(tmp_path, monkeypatch)
        rerun.root = tmp_path / "second"
        rerun()
        assert paths.finished(rerun.device) and holder.poll() is None
    finally:
        holder.stdin.close()
        holder.wait(10)


def test_today_a_device_knows_no_serial_of_its_own():
    assert not hasattr(Device(pathlib.Path("."), False, False), "serial")
