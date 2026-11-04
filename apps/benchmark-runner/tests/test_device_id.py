import pathlib
import re
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from device.identity import DeviceIdError, device_id  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[3]
# Real block of a capture taken before the identity fields existed.
OLD_HOST = {"model": "", "manufacturer": "", "hardware": "", "sdkInt": 0, "release": "", "javaVersion": "25.0.3", "defaultKeySizeProperty": ""}
HOST = dict(OLD_HOST, fingerprint="", javaVendor="Eclipse Adoptium", javaRuntimeVersion="25.0.3+9-LTS", osName="Mac OS X", osArch="aarch64")
ANDROID = {"model": "Pixel 9", "manufacturer": "Google", "hardware": "zuma", "sdkInt": 36, "release": "16", "javaVersion": "0",
           "fingerprint": "google/tokay/tokay:16/BP3A.250905.014/13718934:user/release-keys"}


def test_android_shape():
    assert re.fullmatch(r"pixel-9-api36-[0-9a-f]{8}", device_id(ANDROID))


def test_host_shape():
    assert re.fullmatch(r"host-mac-os-x-aarch64-jdk25-[0-9a-f]{8}", device_id(HOST))


# Real blocks and ids from discovery runs; an id changing here orphans results.
@pytest.mark.parametrize("runtime, expected", [
    ({"model": "sdk_gphone_arm64", "manufacturer": "Google", "hardware": "ranchu", "sdkInt": 30, "release": "11", "javaVersion": "0",
      "defaultKeySizeProperty": "", "fingerprint": "google/sdk_gphone_arm64/emulator_arm64:11/RSR1.240422.006/12134477:userdebug/dev-keys",
      "javaVendor": "The Android Project", "javaRuntimeVersion": "0.9", "osName": "Linux", "osArch": "aarch64"},
     "sdk-gphone-arm64-api30-841c21cf"),
    (HOST, "host-mac-os-x-aarch64-jdk25-598f8c72"),
    (dict(HOST, javaVersion="17.0.20.1", javaRuntimeVersion="17.0.20.1+1"), "host-mac-os-x-aarch64-jdk17-98b06548"),
])
def test_ids_of_real_runtime_blocks(runtime, expected):
    assert device_id(runtime) == expected


def test_an_os_update_gives_a_new_id():
    assert device_id(ANDROID) != device_id(dict(ANDROID, fingerprint=ANDROID["fingerprint"].replace("13718934", "13718935")))


def test_host_hash_covers_vendor_and_runtime_version():
    assert device_id(HOST) != device_id(dict(HOST, javaVendor="Other"))
    assert device_id(HOST) != device_id(dict(HOST, javaRuntimeVersion="25.0.3+10-LTS"))


def test_only_the_build_identity_is_hashed():
    assert device_id(ANDROID) == device_id(dict(ANDROID, hardware="other", manufacturer="other", javaVersion="1"))
    assert device_id(HOST) != device_id(dict(HOST, osArch="x86_64"))


def test_an_existing_android_capture_is_refused():
    runtime = yaml.safe_load((REPO / "apps/perf-repair/tests/fixtures/runtimes/android36/probe.yaml").read_text())["runtime"]
    with pytest.raises(DeviceIdError, match="device_id_fields_missing: runtime lacks model, fingerprint;"):
        device_id(runtime)


@pytest.mark.parametrize("runtime, missing", [
    (OLD_HOST, "osName, osArch, javaVendor, javaRuntimeVersion"),
    ({k: v for k, v in ANDROID.items() if k != "fingerprint"}, "fingerprint"),
    (dict(ANDROID, model=""), "model"),
    ({}, "osName, osArch, javaVersion, javaVendor, javaRuntimeVersion"),
])
def test_absent_fields_are_refused_never_invented(runtime, missing):
    with pytest.raises(DeviceIdError, match=f"device_id_fields_missing: runtime lacks {missing};"):
        device_id(runtime)


@pytest.mark.parametrize("runtime, code", [
    (dict(ANDROID, model="+++"), "device_id_empty_slug"),
    (dict(HOST, javaVersion="unknown"), "device_id_bad_java_version"),
    (dict(ANDROID, sdkInt="x"), "device_id_bad_sdk"),
])
def test_unusable_values_are_refused(runtime, code):
    with pytest.raises(DeviceIdError, match=code):
        device_id(runtime)
