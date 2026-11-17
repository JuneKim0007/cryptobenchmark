import subprocess

import pytest

from cryptobench.shared.device import probe
from cryptobench.shared.device.adb import DeviceError, DeviceLost

# hand-written: what adb devices -l prints for every state the probe classifies
LISTING = """* daemon not running; starting now at tcp:5038
* daemon started successfully
List of devices attached
56301AAAA00001         device usb:1-1 product:frankel model:Pixel_10 device:frankel transport_id:3
emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1
R58N00000001           unauthorized usb:1-2 transport_id:4
192.168.1.5:5555       offline transport_id:5
????????????           no permissions (user in plugdev group; are your udev rules wrong?); see [http://developer.android.com/tools/device.html] usb:1-3 transport_id:6
0123456789ABCDEF       recovery usb:1-4 transport_id:7
emulator-5556          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:8
HT0000000002           device usb:2-1 product:x model:Old_Phone device:x transport_id:9

"""


def getprop(**props):
    return "".join(f"[{key}]: [{value}]\n" for key, value in props.items())


PROPS = {
    "56301AAAA00001": getprop(**{"ro.serialno": "56301AAAA00001", "ro.product.model": "Pixel 10", "ro.build.version.sdk": "37", "sys.boot_completed": "1"}),
    "emulator-5554": getprop(**{"ro.kernel.qemu": "1", "ro.boot.qemu.avd_name": "cb-api33", "ro.product.model": "sdk_gphone64_arm64",
                                "ro.build.version.sdk": "33", "sys.boot_completed": "1", "ro.serialno": "EMULATOR35X1X11X0"}),
    "emulator-5556": getprop(**{"ro.boot.qemu": "1", "ro.build.version.sdk": "30", "sys.boot_completed": ""}),
    "HT0000000002": getprop(**{"ro.serialno": "unknown", "ro.product.model": "Old Phone", "ro.build.version.sdk": "26", "sys.boot_completed": "1"}),
}


def fake_adb(listing=LISTING, props=PROPS, lost=()):
    def adb(*arguments):
        if arguments == ("devices", "-l"):
            return subprocess.CompletedProcess(arguments, 0, listing, "")
        serial = arguments[1]
        if serial in lost:
            return subprocess.CompletedProcess(arguments, 1, "", f"error: device '{serial}' not found")
        return subprocess.CompletedProcess(arguments, 0, props[serial], "")
    return adb


def by_transport(rows):
    return {row.transport: row for row in rows}


def test_every_state_is_classified_with_its_code():
    rows = by_transport(probe.enumerate_devices(fake_adb()))
    codes = {serial: row.reason.split(":", 1)[0] if row.reason else "ready" for serial, row in rows.items()}
    assert codes == {"56301AAAA00001": "ready", "emulator-5554": "ready", "R58N00000001": "device_unauthorized",
                     "192.168.1.5:5555": "device_offline", "????????????": "device_no_permissions", "0123456789ABCDEF": "device_not_booted",
                     "emulator-5556": "device_not_booted", "HT0000000002": "ready"}
    assert rows["????????????"].state == "no permissions" and "plugdev" in rows["????????????"].reason


def test_keys_are_the_serialno_or_the_avd_and_an_untrusted_one_is_the_transport():
    rows = by_transport(probe.enumerate_devices(fake_adb()))
    assert rows["56301AAAA00001"].key == "56301AAAA00001" and rows["56301AAAA00001"].note is None
    assert (rows["emulator-5554"].key, rows["emulator-5554"].kind, rows["emulator-5554"].sdk) == ("emulator:cb-api33", "emulator", 33)
    assert rows["HT0000000002"].key == "HT0000000002" and rows["HT0000000002"].note.startswith("unstable_id: HT0000000002: ro.serialno is unknown")
    assert (rows["192.168.1.5:5555"].connection, rows["56301AAAA00001"].connection, rows["emulator-5554"].connection) == ("tcp", "usb", "emulator")


def test_two_devices_with_one_serialno_are_both_unstable():
    props = {**PROPS, "HT0000000002": PROPS["56301AAAA00001"]}
    rows = by_transport(probe.enumerate_devices(fake_adb(props=props)))
    assert [rows[s].key for s in ("56301AAAA00001", "HT0000000002")] == ["56301AAAA00001", "HT0000000002"]
    assert all(rows[s].note.startswith(f"unstable_id: {s}: 56301AAAA00001 names 2 devices") for s in ("56301AAAA00001", "HT0000000002"))


def test_an_emulator_without_an_avd_name_is_unstable():
    props = {**PROPS, "emulator-5554": getprop(**{"ro.kernel.qemu": "1", "ro.build.version.sdk": "26", "sys.boot_completed": "1"})}
    row = by_transport(probe.enumerate_devices(fake_adb(props=props)))["emulator-5554"]
    assert row.key == "emulator-5554" and row.note.startswith("unstable_id: emulator-5554: the emulator names no AVD")


def test_a_device_lost_before_its_getprop_is_offline():
    row = by_transport(probe.enumerate_devices(fake_adb(lost=("56301AAAA00001",))))["56301AAAA00001"]
    assert row.reason.startswith("device_offline: 56301AAAA00001 did not answer getprop")


def test_a_failed_listing_is_coded():
    dead = lambda *a: subprocess.CompletedProcess(a, 1, "", "cannot connect to daemon at tcp:5038")
    with pytest.raises(DeviceLost, match="^device_lost: adb devices -l: cannot connect to daemon"):
        probe.enumerate_devices(dead)
    odd = lambda *a: subprocess.CompletedProcess(a, 1, "", "unexpected")
    with pytest.raises(DeviceError, match="^adb devices -l: unexpected"):
        probe.enumerate_devices(odd)


def test_nothing_attached_is_an_empty_listing():
    assert probe.enumerate_devices(fake_adb(listing="List of devices attached\n\n")) == []
    assert probe.listing([], {}) == ["devices:   0 ready, 0 not ready"]


def test_the_listing_shows_aliases_then_each_reason_and_note():
    lines = probe.listing(probe.enumerate_devices(fake_adb()), {"pixel10": "56301AAAA00001"})
    assert lines[0] == "devices:   3 ready, 5 not ready"
    assert lines[1].split() == ["key", "alias", "kind", "model", "api", "connection", "state"]
    assert lines[2].split()[:3] == ["56301AAAA00001", "pixel10", "physical"]
    assert any(line.startswith("  device_unauthorized: R58N00000001 is unauthorized; unlock") for line in lines)
    assert any(line.startswith("  unstable_id: HT0000000002") for line in lines)
