from pathlib import Path

import pytest

from cryptobench.shared.device.probe import DeviceRow
from cryptobench.shared.errors.input_error import InputError
from cryptobench.shared.session import document, targets

PIXEL = DeviceRow("56301AAAA00001", "56301AAAA00001", "device", "physical", "Pixel 10", 37, "usb")
EMU = DeviceRow("emulator:cb-api33", "emulator-5554", "device", "emulator", "sdk", 33, "emulator")
SAMSUNG = DeviceRow("R58N00000001", "R58N00000001", "unauthorized", connection="usb",
                    reason="device_unauthorized: R58N00000001 is unauthorized; unlock the device and accept its USB debugging prompt")
OLD = DeviceRow("HT0000000002", "HT0000000002", "device", "physical", "Old", 26, "usb", note="unstable_id: HT0000000002: ro.serialno is unknown")
ROWS = [PIXEL, EMU, SAMSUNG, OLD]


@pytest.fixture
def folder(tmp_path):
    for name in ("global.yaml", "host.yaml", "tier1.yaml", "tier2.yaml", "other/tier1.yaml"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("schemaVersion: 1\n")
    return tmp_path


def session(folder, text):
    path = folder / "session.yaml"
    path.write_text("schemaVersion: 1\n" + text)
    return document.parse(path)


def resolved(folder, text, rows=ROWS, aliases=None):
    return targets.resolve(session(folder, text), rows, aliases or {}, lambda: folder / "global.yaml")


def by_name(result):
    return {t.name: t for t in result.targets}


def test_select_all_runs_every_ready_physical_device_with_the_defaults(folder):
    result = resolved(folder, "defaults: {suites: [tier1.yaml]}\n")
    assert [(t.name, t.key, t.transport, t.order) for t in result.targets] == [("56301AAAA00001", "56301AAAA00001", "56301AAAA00001", 0),
                                                                               ("HT0000000002", "HT0000000002", "HT0000000002", 0)]
    assert by_name(result)["HT0000000002"].unstable and by_name(result)["56301AAAA00001"].config == folder / "global.yaml"
    assert result.notices == ["host_benchmark_not_set: host.benchmark is false"]


def test_emulators_join_select_all_only_when_asked(folder):
    assert "emulator:cb-api33" in by_name(resolved(folder, "devices: {emulators: true}\ndefaults: {suites: [tier1.yaml]}\n"))


def test_listed_selects_by_key_alias_or_serial_and_a_listed_emulator_runs(folder):
    text = "devices: {select: listed}\ndefaults: {suites: [tier1.yaml]}\ntargets:\n  pixel10: {}\n  emulator-5554: {order: 1}\n"
    result = resolved(folder, text, aliases={"pixel10": "56301AAAA00001"})
    assert [(t.name, t.key, t.order) for t in result.targets] == [("pixel10", "56301AAAA00001", 0), ("emulator-5554", "emulator:cb-api33", 1)]


@pytest.mark.parametrize("target, line", [
    ("nosuch: {}", "device_not_attached: nosuch: adb lists no such key, alias or serial; attached: "),
    ("R58N00000001: {}", "device_unauthorized: R58N00000001 is unauthorized"),
    ("56301AAAA00001: {order: -1}", "invalid_order: 56301AAAA00001: -1; use an integer >= 0"),
    ("56301AAAA00001: {order: 1.5}", "invalid_order: 56301AAAA00001: 1.5"),
    ("56301AAAA00001: {order: 'two'}", "invalid_order: 56301AAAA00001: 'two'"),
    ("56301AAAA00001: {order: true}", "invalid_order: 56301AAAA00001: True"),
    ("56301AAAA00001: {config: missing.yaml}", "missing_file: "),
    ("56301AAAA00001: {suites: []}", "nothing_to_measure: 56301AAAA00001: no suites"),
    ("56301AAAA00001: {suites: [absent.yaml]}", "missing_file: "),
    ("56301AAAA00001: {suites: [tier1.yaml, other/tier1.yaml]}", "target_conflict: 56301AAAA00001: suites "),
])
def test_one_bad_target_is_skipped_with_its_code_and_the_others_run(folder, target, line):
    result = resolved(folder, f"devices: {{select: listed}}\ndefaults: {{suites: [tier1.yaml]}}\ntargets:\n  {target}\n  HT0000000002: {{}}\n")
    assert [name for name, _ in result.skipped] == [target.split(":")[0]]
    assert result.skipped[0][1].startswith(line), result.skipped[0][1]
    assert [t.name for t in result.targets] == ["HT0000000002"]


def test_a_named_config_that_is_missing_never_falls_back(folder):
    result = resolved(folder, "defaults: {config: absent.yaml, suites: [tier1.yaml]}\ndevices: {select: listed}\ntargets: {HT0000000002: {}}\n")
    assert result.skipped == [("HT0000000002", f"missing_file: {folder / 'absent.yaml'} (defaults.config)")]


def test_two_names_for_one_device_skip_both(folder):
    result = resolved(folder, "defaults: {suites: [tier1.yaml]}\ntargets:\n  pixel10: {}\n  56301AAAA00001: {}\n", aliases={"pixel10": "56301AAAA00001"})
    assert sorted(result.skipped) == [("56301AAAA00001", "target_conflict: pixel10 and 56301AAAA00001 name one device, 56301AAAA00001"),
                                      ("pixel10", "target_conflict: pixel10 and 56301AAAA00001 name one device, 56301AAAA00001")]


def test_the_host_runs_after_the_last_phone_group_unless_its_order_is_set(folder):
    text = "host: {benchmark: true}\ndefaults: {suites: [tier1.yaml], order: 0}\ntargets:\n  56301AAAA00001: {order: 2}\n  host: {config: host.yaml}\n"
    host = by_name(resolved(folder, text))["host"]
    assert (host.order, host.transport, host.config) == (3, None, folder / "host.yaml")
    assert by_name(resolved(folder, text.replace("{config: host.yaml}", "{config: host.yaml, order: 0}")))["host"].order == 0
    assert by_name(resolved(folder, "host: {benchmark: true}\ndefaults: {suites: [tier1.yaml]}\n", rows=[]))["host"].order == 0


def test_a_listed_host_without_host_benchmark_is_skipped_with_the_notice(folder):
    result = resolved(folder, "defaults: {suites: [tier1.yaml]}\ntargets: {host: {}}\n", rows=[])
    assert result.skipped == [("host", "host_benchmark_not_set: host.benchmark is false")]
    assert str(targets.nothing_to_measure(result)).startswith("nothing_to_measure: no device target is ready or resolved; host.benchmark is false")


def test_groups_follow_ascending_order(folder):
    text = "devices: {emulators: true}\nhost: {benchmark: true}\ndefaults: {suites: [tier1.yaml]}\ntargets:\n  emulator:cb-api33: {order: 1}\n"
    assert [[t.name for t in g] for g in targets.groups(resolved(folder, text).targets)] == [["56301AAAA00001", "HT0000000002"], ["emulator:cb-api33"], ["host"]]


@pytest.mark.parametrize("text, code", [
    ("devices: {select: some}\n", "wrong_type"),
    ("devices: {emulators: 'yes'}\n", "wrong_type"),
    ("devices: {probe: true}\n", "unknown_keys"),
    ("targets: [a]\n", "not_a_mapping"),
    ("targets: {a: {suite: [x]}}\n", "unknown_keys"),
    ("defaults: {suites: tier1.yaml}\n", "wrong_type"),
    ("defaults: {config: 3}\n", "wrong_type"),
    ("name: 'a/b'\n", "wrong_type"),
    ("extra: 1\n", "unknown_keys"),
])
def test_a_session_file_that_cannot_be_read_stops(folder, text, code):
    with pytest.raises(InputError) as refused:
        session(folder, text)
    assert refused.value.code == code


def test_a_missing_session_file_stops(tmp_path):
    with pytest.raises(InputError, match="^missing_file: .*absent.yaml \\(session\\)"):
        document.parse(tmp_path / "absent.yaml")


def test_the_name_defaults_to_the_file_stem(folder):
    assert session(folder, "").name == "session" and session(folder, "name: tiers\n").name == "tiers"
