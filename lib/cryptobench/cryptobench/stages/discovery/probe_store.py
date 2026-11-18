"""--discovery verify: the build key, the stored capture+trial it names, reused unchanged on a match, otherwise the probe runs and its
capture+trial are stored under the key; every path says why it was taken."""
import hashlib
import json
import shutil

from cryptobench.shared import paths
from cryptobench.shared.device.adb import PACKAGE, DeviceError, DeviceLost
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.errors.input_error import InputError
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.log.warn import warn
from cryptobench.shared.results import identity
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stored(folder, value):
    """(the capture, None) when key.yaml names this key and the sha256 of each file it lists; (None, the damaged file) for any other entry
    there; (None, None) when there is none."""
    if not folder.is_dir():
        return None, None
    try:
        recorded = read_yaml(folder / KEY)
    except (OSError, InputError):
        return None, KEY
    files = recorded.get("files")
    captures = [name for name in files if capture_files.CAPTURE.fullmatch(name)] if isinstance(files, dict) else []
    if recorded.get("key") != value or len(captures) != 1 or sorted(files) != sorted(p.name for p in trio(folder / captures[0])):
        return None, KEY
    for path in trio(folder / captures[0]):
        if not path.is_file() or digest(path) != files[path.name]:
            return None, path.name
    return folder / captures[0], None


def differences(store, value):
    """The nested key fields that differ from the newest readable entry of this device fingerprint, for the line that says why the probe runs."""
    fingerprint, same = value["device"]["fingerprint"], []
    for path in (f for f in store.glob(f"*/{KEY}") if not f.parent.name.startswith(".")) if store.is_dir() else []:
        try:
            other = read_yaml(path).get("key")
        except (OSError, InputError):
            continue
        if isinstance(other, dict) and isinstance(other.get("device"), dict) and other["device"].get("fingerprint") == fingerprint:
            same.append((path.stat().st_mtime, path.parent.name, other))
    if not same:
        return f"no stored entry for fingerprint {fingerprint}"
    _, name, other = max(same, key=lambda found: found[:2])
    return f"the newest entry {name} of this fingerprint differs in {', '.join(field[1:] for field in identity.changed(value, other, '.'))}"


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
    capture, damaged = stored(entry, value)
    if damaged:
        say(f"full probe: stored entry {entry.name} is damaged: {damaged}")
        return None, value
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
    """The probe's capture, trial and requirements under the key with their sha256, written whole or not at all, replacing a damaged entry;
    a failed write only warns."""
    entry = store / named(value)
    if stored(entry, value)[0]:
        return
    staging = store / f".staging-{entry.name}"
    try:
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        for source in trio(capture):
            shutil.copy2(source, staging / source.name)
        (staging / KEY).write_text(dump_yaml({"key": value, "files": {p.name: digest(p) for p in trio(staging / capture.name)}}))
        shutil.rmtree(entry, ignore_errors=True)
        staging.rename(entry)
        say(f"stored {entry / capture.name} under key {entry.name}")
    except OSError as error:
        warn(f"probe_store_failed: {entry}: {type(error).__name__}: {one_line(error)}")
