"""Device facts for the settings table: what this device can support, gathered once after install and probe; nothing here decides."""
import zipfile

import yaml

from device import capture as captured, clocks
from device.adb import PACKAGE
from repo import BENCHMARK

FACTS = "facts.yaml"
NATIVE_LIBRARY = "libaffinity.so"
APK = BENCHMARK / "modules/android/build/outputs/apk/release/android-release.apk"


def rooted(device):
    return "uid=0" in device.run("shell", "timeout 5 su -c id", check=False).stdout


def installed_abi(device):
    dump = device.run("shell", f"pm dump {PACKAGE} | grep -m1 primaryCpuAbi", check=False).stdout
    abi = dump.split("=", 1)[1].strip() if "=" in dump else ""
    return abi if abi and abi != "null" else device.shell("getprop ro.product.cpu.abi").strip()


def pinning(apk, abi):
    """None when the release APK is absent: unknown, never a false no_pinning."""
    if not apk.is_file():
        print(f"warning: pinning_unknown: {apk} absent; facts.yaml records pinning null")
        return None
    with zipfile.ZipFile(apk) as archive:
        return f"lib/{abi}/{NATIVE_LIBRARY}" in archive.namelist()


def collect(device, capture):
    sdk = captured.read_runtime(capture).get("sdkInt")
    return {
        "schemaVersion": 1,
        "os": {"sdkInt": int(sdk) if str(sdk).isdigit() else None},
        "rooted": rooted(device),
        "cpu": {"cores": [{"core": c["index"], "online": c["online"], "maxKhz": c["cpuMaxKhz"]} for c in clocks.read(device)]},
        "pinning": pinning(APK, installed_abi(device)),
    }


def gather(device, discovery, capture):
    path = discovery / FACTS
    path.write_text(yaml.safe_dump(collect(device, capture), sort_keys=False))
    return path
