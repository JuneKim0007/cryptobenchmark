"""A capture's runtime block, read once for the runner; a capture of another schema version is refused; the guide's name for its platform."""
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.coded import Coded

SCHEMA = 1   # discovery's CapturedEnvironment.SCHEMA_VERSION


class CaptureError(ValueError, Coded):
    pass


def runtime(capture):
    """The runtime block of a loaded capture document."""
    if capture.get("schemaVersion") != SCHEMA:
        raise CaptureError(f"unsupported_capture_schema: {capture.get('schemaVersion')}, this build reads {SCHEMA}")
    return capture.get("runtime") or {}


def read_runtime(path):
    return runtime(read_yaml(path))


def platform(runtime):
    """The guide's name for where this capture ran: android-<sdk>, else jdk-<major> of a host JVM."""
    if runtime.get("sdkInt"):
        return f"android-{runtime['sdkInt']}"
    major = str(runtime.get("javaVersion") or "").split(".")[0]
    return f"jdk-{major}" if major else None
