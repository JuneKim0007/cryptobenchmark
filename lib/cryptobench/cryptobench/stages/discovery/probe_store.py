"""--discovery verify: the build key, the stored capture+trial it names, reused unchanged on a match, otherwise the probe runs and its
capture+trial are stored under the key; every path says why it was taken."""
import hashlib
import json
import shutil

from cryptobench.shared import paths
from cryptobench.shared.device.adb import PACKAGE, DeviceError, DeviceLost
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.log.warn import warn
from cryptobench.stages.discovery import build_versions, capture_files

KEY = "key.yaml"


def trio(capture):
    """A capture and the trial and requirements with its stamp."""
    stamp = capture_files.CAPTURE.fullmatch(capture.name).group(1)
    return capture, paths.Discovery(capture.parent).trial(stamp), capture_files.requirements(capture)


def say(line):
    print(f"discovery: verify: {line}")


def installed_apks(device, package):
    """{apk file name: sha256} of an installed package, read on the device; {} when pm knows no path for it. The install folder is random per install."""
    found = {}
    for line in device.run("shell", f"pm path {package}", check=False).stdout.splitlines():
        if line.startswith("package:"):
            path = line[len("package:"):].strip()
            found[path.rsplit("/", 1)[-1]] = (device.run("shell", f"sha256sum {path}", check=False).stdout.split() or [None])[0]
    return found


def key(device, shipped):
    """(the build key, why it cannot identify this build or None). The installed APKs carry the code and the bundled jars that run."""
    try:
        value = {"device": {"fingerprint": device.identity()["fingerprint"], **build_versions.read(device)},
                 "apk": {package: installed_apks(device, package) for package in (PACKAGE, f"{PACKAGE}.test")},
                 "bundled": shipped}
    except DeviceLost:
        raise
    except DeviceError as error:
        return None, f"the device's build could not be read: {one_line(error)}"
    unread = [p for p, apks in value["apk"].items() if not apks or None in apks.values()]
    missing = [why for why, absent in (
        ("device: no apex versionCode listed", not value["device"]["apex"]),
        (f"apk: pm path printed nothing or sha256sum failed for {', '.join(unread)}", unread)) if absent]
    return value, "; ".join(missing) or None


def named(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def stored(folder):
    """The capture of a complete stored entry, else None."""
    captures = sorted(p for p in paths.Discovery(folder).captures() if capture_files.CAPTURE.fullmatch(p.name)) if folder.is_dir() else []
    if len(captures) != 1 or not (folder / KEY).is_file():
        return None
    return captures[0] if all(p.is_file() for p in trio(captures[0])) else None


def differences(store, value):
    """Which key parts differ from the newest stored entry, for the line that says why the probe runs."""
    entries = sorted(store.glob(f"*/{KEY}"), key=lambda f: f.stat().st_mtime) if store.is_dir() else []
    if not entries:
        return "the store is empty"
    other = read_yaml(entries[-1])
    changed = sorted(part for part in set(value) | set(other) if value.get(part) != other.get(part)) or ["nothing (an incomplete entry)"]
    return f"the newest entry {entries[-1].parent.name} differs in {', '.join(changed)}"


def has_plan_directory(device):
    return device.run("shell", f"ls -d {device.files}", check=False).returncode == 0


def forget_captures(device):
    """The device reads the newest capture and trial by name, so a pushed earlier pair must be the only one there."""
    device.shell("rm -f " + " ".join(f"{device.files}/{prefix}_*.yaml" for prefix in (paths.CAPTURE_PREFIX, paths.TRIAL_PREFIX, paths.REQUIREMENTS_PREFIX)))


def verified(device, discovery, shipped, store):
    """(the reused capture copied into discovery, or None when the probe must run; the key, or None when it is incomplete)."""
    value, missing = key(device, shipped)
    if missing:
        say(f"full probe: the key is incomplete: {missing}")
        return None, None
    entry = store / named(value)
    capture = stored(entry)
    if capture is None:
        say(f"full probe: no stored capture for key {entry.name}; {differences(store, value)}")
        return None, value
    if not has_plan_directory(device):
        say(f"full probe: key {entry.name} matches, but the device has no plan directory; only the probe makes the app create it")
        return None, value
    for source in trio(capture):
        shutil.copy2(source, discovery / source.name)
    forget_captures(device)
    say(f"reused {capture}: key {entry.name} matches (device build and apex versions, installed APKs, providers.bundled); probe skipped")
    return discovery / capture.name, value


def keep(store, value, capture):
    """The probe's capture, trial and requirements under the key, written whole or not at all; a failed write only warns."""
    entry = store / named(value)
    if stored(entry):
        return
    staging = store / f".staging-{entry.name}"
    try:
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        for source in trio(capture):
            shutil.copy2(source, staging / source.name)
        (staging / KEY).write_text(dump_yaml(value))
        shutil.rmtree(entry, ignore_errors=True)
        staging.rename(entry)
        say(f"stored {entry / capture.name} under key {entry.name}")
    except OSError as error:
        warn(f"probe_store_failed: {entry}: {type(error).__name__}: {one_line(error)}")
