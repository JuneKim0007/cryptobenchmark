"""The device folder of a results root a reader names, or the only one there."""
import pathlib

from cryptobench.shared.errors.failures import Stop
from cryptobench.shared import paths


def device_folder(root, wanted=None):
    root = pathlib.Path(root)
    found = paths.Results(root).devices()
    if wanted and wanted not in found:
        raise Stop(f"device_not_in_results: {wanted}; {root} holds {found}")
    if not wanted and not found:
        raise Stop(f"no_device_results: {root} holds no <device_id>/{paths.MANIFEST}; run the pipeline first")
    if not wanted and len(found) > 1:
        raise Stop(f"several_device_results: {root} holds {', '.join(found)}; name one with --device-id")
    return root / (wanted or found[0])
