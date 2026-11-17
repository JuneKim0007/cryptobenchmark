"""The device software a resumed run compares beside the capture's fingerprint: the security patch and the APEX modules the timed calls run on."""
import re

from cryptobench.pipeline.warn import warn
from cryptobench.shared import paths

SECURITY_PATCH = "ro.build.version.security_patch"
# the platform provider and the runtime; a Mainline update replaces them without a new fingerprint
APEX_MODULES = ("com.android.conscrypt", "com.android.art")
TAG = re.compile(r"<apex-info\b([^>]*)>")
ATTRIBUTE = re.compile(r'(\w+)="([^"]*)"')


def read(device):
    return {"securityPatch": security_patch(device), "apex": apex(device)}


def security_patch(device):
    result = device.run("shell", f"getprop {SECURITY_PATCH}", check=False)
    patch = result.stdout.strip() if result.returncode == 0 else ""
    if not patch:
        warn(f"facts_unknown: build.securityPatch: getprop {SECURITY_PATCH} printed nothing; facts.yaml records null")
    return patch or None


def apex(device):
    """{module: active versionCode, None when the device has no such module}; None when the list is unreadable."""
    result = device.run("shell", f"cat {paths.DeviceDirs.APEX_INFO}", check=False)
    active = active_modules(result.stdout if result.returncode == 0 else "")
    if not active:
        warn(f"facts_unknown: build.apex: {paths.DeviceDirs.APEX_INFO} names no active module; facts.yaml records null")
        return None
    return {module: active.get(module) for module in APEX_MODULES}


def active_modules(listing):
    found = {}
    for tag in TAG.findall(listing):
        fields = dict(ATTRIBUTE.findall(tag))
        if fields.get("isActive") == "true" and fields.get("moduleName"):
            version = fields.get("versionCode", "")
            found[fields["moduleName"]] = int(version) if version.isdigit() else version or None
    return found
