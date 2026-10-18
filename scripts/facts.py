"""Device facts for the settings table: what this device can support, gathered once after install and probe; nothing here decides."""
import pathlib, zipfile

import yaml

import clocks

FACTS = "facts.yaml"
NATIVE_LIBRARY = "libaffinity.so"
APK = pathlib.Path(__file__).resolve().parent.parent / "modules/android/build/outputs/apk/release/android-release.apk"
PACKAGE = "io.github.junekim0007.cryptobench"


def rooted(device):
    return "uid=0" in device.run("shell", "timeout 5 su -c id", check=False).stdout


def installed_abi(device):
    dump = device.run("shell", f"pm dump {PACKAGE} | grep -m1 primaryCpuAbi", check=False).stdout
    abi = dump.split("=", 1)[1].strip() if "=" in dump else ""
    return abi if abi and abi != "null" else device.shell("getprop ro.product.cpu.abi").strip()


def pinning(apk, abi):
    if not apk.is_file():
        return False
    with zipfile.ZipFile(apk) as archive:
        return f"lib/{abi}/{NATIVE_LIBRARY}" in archive.namelist()


def collect(device, capture, apk=APK):
    runtime = (yaml.safe_load(capture.read_text()) or {}).get("runtime") or {}
    sdk = runtime.get("sdkInt")
    return {
        "schemaVersion": 1,
        "os": {"sdkInt": int(sdk) if str(sdk).isdigit() else None},
        "rooted": rooted(device),
        "cpu": {"cores": [{"core": c["index"], "online": c["online"], "maxKhz": c["cpuMaxKhz"]} for c in clocks.read(device)]},
        "pinning": pinning(apk, installed_abi(device)),
    }


def gather(device, discovery, capture):
    path = discovery / FACTS
    path.write_text(yaml.safe_dump(collect(device, capture), sort_keys=False))
    return path
