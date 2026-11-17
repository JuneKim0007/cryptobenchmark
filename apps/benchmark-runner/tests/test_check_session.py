"""pipeline.py --check-session end to end against a fake adb: the plan, its skips and notices, nothing written."""
import os, pathlib, subprocess, sys

from test_devices_listing import FAKE_ADB

PIPELINE = pathlib.Path(__file__).resolve().parents[1] / "pipeline.py"


def checked(tmp_path, session):
    tools = tmp_path / "sdk/platform-tools"
    tools.mkdir(parents=True)
    (tools / "adb").write_text(FAKE_ADB)
    (tools / "adb").chmod(0o755)
    for name in ("global.yaml", "tier1.yaml", "tier2.yaml"):
        (tmp_path / name).write_text("schemaVersion: 1\n")
    (tmp_path / "session.yaml").write_text(session)
    env = {**os.environ, "HOME": str(tmp_path), "ANDROID_HOME": str(tmp_path / "sdk")}
    before = sorted(tmp_path.rglob("*"))
    done = subprocess.run([sys.executable, str(PIPELINE), "--check-session", str(tmp_path / "session.yaml"), "--results", str(tmp_path / "results")],
                          env=env, capture_output=True, text=True, timeout=60)
    assert sorted(tmp_path.rglob("*")) == before
    return done


def test_the_plan_lists_groups_skips_and_notices(tmp_path):
    done = checked(tmp_path, "schemaVersion: 1\nname: tiers\ndevices: {emulators: true}\nhost: {benchmark: true}\n"
                             "defaults: {config: global.yaml, suites: [tier1.yaml, tier2.yaml]}\ntargets:\n  R58N1: {}\n  host: {order: 0}\n")
    assert done.returncode == 0, done.stderr
    out = done.stdout.splitlines()
    results = tmp_path / "results"
    assert f"order 0:   emulator:cb-api33 (emulator:cb-api33, adb emulator-5554): tier1, tier2 -> {results}/<device_id>/<suite>/" in out
    assert f"order 0:   host (host): tier1, tier2 -> {results}/<device_id>/<suite>/" in out
    assert "warning: parallel_unavailable: order 0 has 2 targets; they run one after another" in out
    assert any(line.startswith("skipped:   R58N1: device_unauthorized: R58N1 is unauthorized") for line in out)


def test_nothing_to_measure_stops(tmp_path):
    done = checked(tmp_path, "schemaVersion: 1\ndevices: {select: listed}\ndefaults: {config: global.yaml, suites: [tier1.yaml]}\n")
    assert done.returncode == 1
    assert "warning: host_benchmark_not_set: host.benchmark is false" in done.stdout
    assert done.stderr.strip() == "error: nothing_to_measure: no device target is ready or resolved; host.benchmark is false"
