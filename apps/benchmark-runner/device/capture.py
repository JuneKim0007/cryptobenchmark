"""A capture's runtime block, read once for the runner; a capture of another schema version is refused."""
import yaml

SCHEMA = 1   # discovery's CapturedEnvironment.SCHEMA_VERSION


class CaptureError(ValueError):
    pass


def runtime(capture):
    """The runtime block of a loaded capture document."""
    if capture.get("schemaVersion") != SCHEMA:
        raise CaptureError(f"unsupported_capture_schema: {capture.get('schemaVersion')}, this build reads {SCHEMA}")
    return capture.get("runtime") or {}


def read_runtime(path):
    return runtime(yaml.safe_load(path.read_text()) or {})
