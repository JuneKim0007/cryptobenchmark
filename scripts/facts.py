"""Device facts for the settings table: what this device can support, gathered once after the probe; nothing here decides."""
import zipfile

import yaml

import clocks

FACTS = "facts.yaml"
NATIVE_LIBRARY = "libaffinity.so"


def rooted(device):
    return "uid=0" in device.run("shell", "su -c id", check=False).stdout


def pinning(apk, abi):
    if not apk.is_file():
        return False
    with zipfile.ZipFile(apk) as archive:
        return f"lib/{abi}/{NATIVE_LIBRARY}" in archive.namelist()


def collect(device, capture, apk):
    runtime = (yaml.safe_load(capture.read_text()) or {}).get("runtime") or {}
    cores = clocks.read(device)
    abi = device.shell("getprop ro.product.cpu.abi").strip()
    return {
        "schemaVersion": 1,
        "os": {"sdkInt": int(runtime.get("sdkInt") or 0), "release": str(runtime.get("release") or "")},
        "rooted": rooted(device),
        "cpu": {"cores": [{"core": int(c["core"][3:]), "online": c["online"], "maxKhz": c["maxKhz"]} for c in cores],
                "governor": next((c["governor"] for c in cores if c["online"]), "-"),
                "locked": clocks.locked([cores])},
        "pinning": pinning(apk, abi),
    }


def write(path, facts):
    path.write_text(yaml.safe_dump(facts, sort_keys=False))
    return path
