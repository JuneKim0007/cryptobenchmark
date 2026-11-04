"""The device id, derived from a capture's runtime block: one build gives one id, and no serial enters it."""
import hashlib, re

import yaml


class DeviceIdError(Exception):
    pass


def fields(runtime, *names):
    values = [str(runtime.get(name) or "") for name in names]
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise DeviceIdError(f"device_id_fields_missing: runtime lacks {', '.join(missing)}; probe again with this build")
    return values


def slug(text):
    made = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not made:
        raise DeviceIdError(f"device_id_empty_slug: {text!r} has no letter or digit")
    return made


def digest(*identity):
    # The separator keeps two different field splits from hashing alike.
    return hashlib.sha256("\n".join(identity).encode()).hexdigest()[:8]


def java_major(version):
    major = re.match(r"\d+", version)
    if not major:
        raise DeviceIdError(f"device_id_bad_java_version: {version!r}")
    return major.group()


def device_id(runtime):
    sdk = str(runtime.get("sdkInt") or 0)
    if not sdk.isdigit():
        raise DeviceIdError(f"device_id_bad_sdk: {sdk!r}")
    if int(sdk) > 0:
        model, fingerprint = fields(runtime, "model", "fingerprint")
        return f"{slug(model)}-api{sdk}-{digest(fingerprint)}"
    os_name, arch, version, vendor, runtime_version = fields(runtime, "osName", "osArch", "javaVersion", "javaVendor",
                                                             "javaRuntimeVersion")
    return f"host-{slug(os_name)}-{slug(arch)}-jdk{java_major(version)}-{digest(vendor, runtime_version)}"


def capture_id(capture):
    return device_id((yaml.safe_load(capture.read_text()) or {}).get("runtime") or {})
