"""pipeline.py --devices end to end against a fake adb: routed before any config, aliases from the user's devices.yaml."""
import os, pathlib, subprocess, sys

PIPELINE = pathlib.Path(__file__).resolve().parents[1] / "pipeline.py"
FAKE_ADB = """#!/bin/sh
if [ "$1" = devices ]; then printf 'List of devices attached\\nemulator-5554  device product:p model:m device:d transport_id:1\\nR58N1  unauthorized usb:1-2 transport_id:2\\n'; exit 0; fi
printf '[ro.kernel.qemu]: [1]\\n[ro.boot.qemu.avd_name]: [cb-api33]\\n[ro.build.version.sdk]: [33]\\n[sys.boot_completed]: [1]\\n'
"""


def listed(tmp_path, adb=FAKE_ADB, devices=None):
    tools = tmp_path / "sdk/platform-tools"
    tools.mkdir(parents=True)
    if adb is not None:
        (tools / "adb").write_text(adb)
        (tools / "adb").chmod(0o755)
    if devices is not None:
        (tmp_path / ".config/cryptobench").mkdir(parents=True)
        (tmp_path / ".config/cryptobench/devices.yaml").write_text(devices)
    env = {**os.environ, "HOME": str(tmp_path), "ANDROID_HOME": str(tmp_path / "sdk"), "CRYPTOBENCH_CONFIG": str(tmp_path / "absent.yaml")}
    return subprocess.run([sys.executable, str(PIPELINE), "--devices"], env=env, capture_output=True, text=True, timeout=60)


def test_devices_lists_before_any_config(tmp_path):
    done = listed(tmp_path, devices="schemaVersion: 1\naliases: {api33: 'emulator:cb-api33'}\n")
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert lines[0] == "devices:   1 ready, 1 not ready"
    assert lines[2].split()[:3] == ["emulator:cb-api33", "api33", "emulator"]
    assert lines[-1].startswith("  device_unauthorized: R58N1 is unauthorized;")


def test_a_missing_adb_is_one_coded_line(tmp_path):
    done = listed(tmp_path, adb=None)
    assert done.returncode == 1 and done.stderr.strip().startswith("error: missing_file: ") and done.stderr.strip().endswith("(set ANDROID_HOME)")


def test_a_bad_alias_file_stops_the_listing(tmp_path):
    done = listed(tmp_path, devices="schemaVersion: 1\naliases: {a: X, b: X}\n")
    assert done.returncode == 1 and "duplicate_alias:" in done.stderr
