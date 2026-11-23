"""A capture's runtime block, read once for the runner; a capture of another schema version is refused; the guide's name for its platform."""
from cryptobench.shared.document.document import DocumentKind, read_yaml
from cryptobench.shared.errors.input_error import InputError

SCHEMA = 1   # contract's CapturedEnvironment.SCHEMA_VERSION


class CaptureError(InputError):
    pass


CAPTURE_DOC = DocumentKind("capture", SCHEMA, CaptureError)


def runtime(capture):
    """The runtime block of a loaded capture document."""
    return CAPTURE_DOC.check(capture).get("runtime") or {}


def read_runtime(path):
    return runtime(read_yaml(path))


def platform(runtime):
    """The guide's name for where this capture ran: android-<sdk>, else jdk-<major> of a host JVM."""
    if runtime.get("sdkInt"):
        return f"android-{runtime['sdkInt']}"
    major = str(runtime.get("javaVersion") or "").split(".")[0]
    return f"jdk-{major}" if major else None
