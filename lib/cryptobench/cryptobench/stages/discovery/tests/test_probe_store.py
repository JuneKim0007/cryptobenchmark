"""--discovery verify on a fake device: the first build probes and stores its capture+trial, the same build reuses them unchanged with the
device's older pair removed, and any change or unreadable key part probes again, saying why."""
import itertools
import os
import types

import pytest
import yaml

from cryptobench.stages.discovery import build_versions, discover, probe_store
from test_manifest import RUNTIME

APEX = '<apex-info moduleName="com.android.conscrypt" versionCode="2" isActive="true"/><apex-info moduleName="com.android.art" versionCode="1" isActive="true"/>'


class Device:
    """install, the probe (a new stamp each time), the build reads and the plan directory, logged."""
    files = "/sdcard/plan"

    def __init__(self, apex=APEX, plan_directory=True, installed="/data/app/~~a1==/pkg-b2==", fingerprint="f/p:17/X/1", sdk=36, packages=""):
        self.apex, self.plan_directory, self.installed, self.fingerprint, self.sdk = apex, plan_directory, installed, fingerprint, sdk
        self.packages = packages
        self.log, self.stamps = [], (f"20260101T00000{n}Z" for n in itertools.count())

    def install(self, _properties):
        self.log.append("install")

    def probe(self, discovery):
        stamp = next(self.stamps)
        self.log.append(f"probe {stamp}")
        for kind, document in (("probe", {"schemaVersion": 1, "runtime": RUNTIME, "providers": []}), ("trial", {"schemaVersion": 1}),
                               ("requirements", {"schemaVersion": 1})):
            (discovery / f"{kind}_{stamp}.yaml").write_text(yaml.safe_dump(document))

    def identity(self):
        return {"sdkInt": self.sdk, "model": "m", "fingerprint": self.fingerprint}

    def run(self, *arguments, check=True):
        command = arguments[1]
        if command.startswith("pm path "):
            out = "".join(f"package:{self.installed}/{command.split()[-1]}/{apk}\n" for apk in ("base.apk", "split_config.arm64_v8a.apk"))
        elif command.startswith("sha256sum "):
            out = f"{'ab' * 32}  {command.split()[-1]}\n"
        elif command == f"getprop {build_versions.SECURITY_PATCH}":
            out = "2026-11-05\n"
        elif command == f"cat {build_versions.paths.DeviceDirs.APEX_INFO}":
            out = self.apex
        elif command == build_versions.PM_APEX:
            out = self.packages
        elif command.startswith("ls -d "):
            return types.SimpleNamespace(returncode=0 if self.plan_directory else 1, stdout="", stderr="")
        else:
            raise AssertionError(command)
        return types.SimpleNamespace(returncode=0, stdout=out, stderr="")

    def shell(self, command):
        assert command.startswith(f"rm -f {self.files}/probe_*.yaml {self.files}/trial_*.yaml {self.files}/requirements_*.yaml"), command
        self.log.append("forget captures")
        return ""


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr(discover, "probe", lambda device, discovery, _waits, _arguments: device.probe(discovery))
    monkeypatch.setattr(discover.facts, "gather", lambda _device, discovery, _capture, _build: discovery / "facts.yaml")
    monkeypatch.setattr(discover.bundled, "check_effective", lambda *_arguments: None)

    def configure(arguments, _stacktrace, _stream=False, *, main_class, **_options):
        configured = tmp_path / "results" / "configuration"
        configured.mkdir(parents=True, exist_ok=True)
        (configured / "effective.yaml").write_text("schemaVersion: 1\nproviders: {}\n")
        return [str(configured / "effective.yaml")]
    monkeypatch.setattr(discover.gradle_runner, "run", configure)
    options = types.SimpleNamespace(discovery="verify", probe_store=str(tmp_path / "store"), stacktrace=False, stream=False, reconnect_wait_minutes=None,
                                    reconnect_poll_seconds=None)

    def once(device):
        results = tmp_path / "results"
        discover.discover_in_place(options, tmp_path / "global.yaml", device, results, [])
        return sorted(p.name for p in (results / "discovery").glob("probe_*.yaml"))
    return once


def test_the_first_build_probes_and_stores_then_the_same_build_reuses_the_pair_unchanged(run, tmp_path, capsys):
    first = Device()
    assert run(first) == ["probe_20260101T000000Z.yaml"] and first.log == ["install", "probe 20260101T000000Z"]
    entries = list((tmp_path / "store").iterdir())
    assert len(entries) == 1 and sorted(p.name for p in entries[0].iterdir()) == [
        "key.yaml", "probe_20260101T000000Z.yaml", "requirements_20260101T000000Z.yaml", "trial_20260101T000000Z.yaml"]
    again = Device()
    assert run(again) == ["probe_20260101T000000Z.yaml"] and again.log == ["install", "forget captures"]
    out = capsys.readouterr().out
    assert "discovery: verify: full probe: no stored capture for key " in out and "no stored entry for fingerprint f/p:17/X/1" in out
    assert f"discovery: verify: reused {entries[0]}/probe_20260101T000000Z.yaml: key {entries[0].name} matches" in out
    assert (tmp_path / "results/discovery/probe_20260101T000000Z.yaml").read_bytes() == (entries[0] / "probe_20260101T000000Z.yaml").read_bytes()


def test_a_changed_apex_probes_again_and_says_which_part_differs(run, capsys):
    run(Device())
    changed = Device(apex=APEX.replace('versionCode="2"', 'versionCode="3"'))
    run(changed)
    assert changed.log == ["install", "probe 20260101T000000Z"]
    assert "of this fingerprint differs in device.apex.com.android.conscrypt\n" in capsys.readouterr().out


def test_the_reason_names_the_nested_fields_that_differ_from_the_newest_entry_of_the_same_fingerprint(run, tmp_path, capsys):
    art = APEX.replace('versionCode="1"', 'versionCode="5"')
    for n, device in enumerate((Device(), Device(apex=art), Device(fingerprint="f/p:17/Y/2"))):
        run(device)
        newest = max((tmp_path / "store").glob("*/key.yaml"), key=lambda f: f.stat().st_mtime_ns)
        os.utime(newest, (n, n))
    assert "; no stored entry for fingerprint f/p:17/Y/2\n" in capsys.readouterr().out
    run(Device(apex=art.replace('versionCode="2"', 'versionCode="3"')))
    assert capsys.readouterr().out.count("of this fingerprint differs in device.apex.com.android.conscrypt\n") == 1


@pytest.mark.parametrize("break_it, why", [
    (lambda device: setattr(device, "apex", ""), "the key is incomplete: device: no apex versionCode listed"),
    (lambda device: setattr(device, "plan_directory", False), "but the device has no plan directory"),
], ids=["no apex", "no plan directory"])
def test_anything_the_key_cannot_vouch_for_falls_back_to_the_probe(run, capsys, break_it, why):
    run(Device())
    device = Device()
    break_it(device)
    run(device)
    assert device.log == ["install", "probe 20260101T000000Z"] and why in capsys.readouterr().out


def test_two_installs_of_the_same_build_differing_only_in_their_random_folders_give_one_key():
    one, other = Device(installed="/data/app/~~Xq3Zw==/pkg-Yt7=="), Device(installed="/data/app/~~Lm0Rr==/pkg-Pa9==")
    build = {"securityPatch": "2026-11-05", "apex": {"com.android.conscrypt": 2, "com.android.art": 1}}
    first, second = probe_store.key(one, [], build), probe_store.key(other, [], build)
    assert first == second and first[1] is None
    assert sorted(first[0]["apk"][probe_store.PACKAGE]) == ["base.apk", "split_config.arm64_v8a.apk"]


def first_lines(path):
    lines = path.read_text().splitlines(keepends=True)
    path.write_text("".join(lines[:len(lines) // 2]))


@pytest.mark.parametrize("damage, prefix", [
    (first_lines, "probe"),
    (first_lines, "trial"),
    (lambda path: path.write_text(""), "requirements"),
    (lambda path: path.unlink(), "trial"),
    (lambda path: path.write_text(yaml.safe_dump(yaml.safe_load(path.read_text())["key"])), "key"),
], ids=["truncated capture", "truncated trial", "empty file", "missing file", "key.yaml without digests"])
def test_a_damaged_entry_is_named_probed_again_and_replaced(run, tmp_path, capsys, damage, prefix):
    run(Device())
    entry = next((tmp_path / "store").iterdir())
    damaged = next(entry.glob(f"{prefix}*.yaml"))
    damage(damaged)
    device = Device()
    assert run(device) == ["probe_20260101T000000Z.yaml"] and device.log == ["install", "probe 20260101T000000Z"]
    assert f"discovery: verify: full probe: stored entry {entry.name} is damaged: {damaged.name}\n" in capsys.readouterr().out
    again = Device()
    run(again)
    assert again.log == ["install", "forget captures"] and [p.name for p in (tmp_path / "store").iterdir()] == [entry.name]


def test_below_sdk_29_the_key_is_complete_so_the_second_run_reuses(run, capsys):
    run(Device(apex="", sdk=26))
    again = Device(apex="", sdk=26)
    run(again)
    assert again.log == ["install", "forget captures"] and "incomplete" not in capsys.readouterr().out


def test_on_android_10_the_package_manager_completes_the_key_so_the_second_run_reuses(run, capsys):
    packages = "package:com.android.conscrypt versionCode:291900000\npackage:com.android.runtime.release versionCode:290000000\n"
    run(Device(apex="", sdk=29, packages=packages))
    again = Device(apex="", sdk=29, packages=packages)
    run(again)
    out = capsys.readouterr().out
    assert again.log == ["install", "forget captures"] and "incomplete" not in out and "facts_unknown: build.apex" not in out


def test_an_unreadable_apex_list_is_read_and_warned_once_per_run(run, capsys):
    run(Device(apex=""))
    assert capsys.readouterr().out.count("facts_unknown: build.apex") == 1
