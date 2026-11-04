"""The device folder of a results root a reader names, or the only one there."""
import pathlib

from failure import fail
from results.layout import MANIFEST


def device_folders(root):
    root = pathlib.Path(root)
    return sorted(p.name for p in root.iterdir() if (p / MANIFEST).is_file()) if root.is_dir() else []


def device_folder(root, wanted=None):
    root = pathlib.Path(root)
    found = device_folders(root)
    if wanted and wanted not in found:
        fail(f"device_not_in_results: {wanted}; {root} holds {found}")
    if not wanted and not found:
        fail(f"no_device_results: {root} holds no <device_id>/{MANIFEST}; run the pipeline first")
    if not wanted and len(found) > 1:
        fail(f"several_device_results: {root} holds {', '.join(found)}; name one with --device-id")
    return root / (wanted or found[0])
