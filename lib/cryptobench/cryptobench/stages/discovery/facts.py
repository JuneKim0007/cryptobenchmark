"""Device facts, gathered once after install and probe: what this device can support, for the settings table, and its build versions, for a
resumed run's identity; nothing here decides."""
import zipfile

from cryptobench.pipeline.warn import warn
from cryptobench.shared.device import capture as captured, clocks
from cryptobench.shared.device.adb import PACKAGE
from cryptobench.shared import paths
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.stages.discovery import build_versions

NATIVE_LIBRARY = "libaffinity.so"
APK = paths.repo().apk


def rooted(device):
    return "uid=0" in device.run("shell", "timeout 5 su -c id", check=False).stdout


def installed_abi(device):
    dump = device.run("shell", f"pm dump {PACKAGE} | grep -m1 primaryCpuAbi", check=False).stdout
    abi = dump.split("=", 1)[1].strip() if "=" in dump else ""
    return abi if abi and abi != "null" else device.shell("getprop ro.product.cpu.abi").strip()


def pinning(apk, abi):
    """None when the release APK is absent: unknown, never a false no_pinning."""
    if not apk.is_file():
        warn(f"pinning_unknown: {apk} absent; facts.yaml records pinning null")
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
        "build": build_versions.read(device),
    }


def gather(device, discovery, capture):
    path = paths.Discovery(discovery).facts
    path.write_text(dump_yaml(collect(device, capture)))
    return path
