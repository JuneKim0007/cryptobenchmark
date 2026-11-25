"""Which devices adb sees: each transport classified ready or not with its fix, keyed by ro.serialno or emulator:<avd>; an id that cannot be
trusted keeps the transport serial and an unstable_id note."""
from __future__ import annotations

import collections
import dataclasses
import re

from cryptobench.shared.device.adb import call_error

READY = "device"
PHYSICAL, EMULATOR = "physical", "emulator"
# adb's state word -> (code, fix); a state not listed is not booted into Android
NOT_READY = {
    "unauthorized": ("device_unauthorized", "unlock the device and accept its USB debugging prompt"),
    "authorizing": ("device_unauthorized", "unlock the device and accept its USB debugging prompt"),
    "offline": ("device_offline", "replug it or run adb reconnect; an emulator still booting comes online by itself"),
    "connecting": ("device_offline", "replug it or run adb reconnect; an emulator still booting comes online by itself"),
    "no permissions": ("device_no_permissions", "add a udev rule for its USB vendor id and put the user in plugdev, then replug"),
}
NOT_BOOTED = ("device_not_booted", "boot it into Android and wait for the home screen")
GETPROP = re.compile(r"^\[([^\]]+)\]: \[(.*)\]$")
FIELD = re.compile(r"^([a-z_]+):(\S*)$")
TCP = re.compile(r"^[\w.-]+:\d+$|\._adb-tls-connect\._tcp")
UNSET = ("", "unknown")


@dataclasses.dataclass(frozen=True)
class DeviceRow:
    key: str
    transport: str
    state: str
    kind: str | None = None
    model: str | None = None
    sdk: int | None = None
    connection: str | None = None
    # the coded line that keeps it from running, with its fix; None: ready
    reason: str | None = None
    # unstable_id: the key is the transport serial, so nothing resumes on it
    note: str | None = None

    @property
    def ready(self) -> bool:
        return self.reason is None


def transports(listing: str) -> list[tuple[str, str, dict[str, str]]]:
    """(serial, state, fields) per line of `adb devices -l`; adb's own messages and the header are skipped."""
    found = []
    for line in listing.splitlines():
        if not line.strip() or line.startswith(("*", "List of devices")):
            continue
        serial, _, rest = line.strip().partition(" ") if "\t" not in line else line.strip().partition("\t")
        rest = rest.strip()
        state = "no permissions" if rest.startswith("no permissions") else rest.split(" ", 1)[0]
        fields = dict(m.groups() for m in map(FIELD.match, rest.split()) if m)
        found.append((serial, state, fields))
    return found


def properties(getprop: str) -> dict[str, str]:
    return dict(m.groups() for m in map(GETPROP.match, getprop.splitlines()) if m)


def connection(serial: str, fields: dict[str, str], kind: str | None) -> str:
    if kind == EMULATOR or serial.startswith("emulator-"):
        return EMULATOR
    if TCP.search(serial):
        return "tcp"
    return "usb" if "usb" in fields else "unknown"


def classify(serial: str, state: str, fields: dict[str, str], props: dict[str, str] | None) -> DeviceRow:
    """One transport as a row; props is its getprop dump, None when adb could not read it."""
    base = {"key": serial, "transport": serial, "state": state, "model": fields.get("model", "").replace("_", " ") or None}
    if state != READY:
        code, fix = NOT_READY.get(state, NOT_BOOTED)
        return DeviceRow(**base, connection=connection(serial, fields, None), reason=f"{code}: {serial} is {state}; {fix}")
    if props is None:
        return DeviceRow(**base, connection=connection(serial, fields, None), reason=f"device_offline: {serial} did not answer getprop; {NOT_READY['offline'][1]}")
    kind = EMULATOR if serial.startswith("emulator-") or "1" in (props.get("ro.kernel.qemu"), props.get("ro.boot.qemu")) else PHYSICAL
    sdk = props.get("ro.build.version.sdk", "")
    row = DeviceRow(**{**base, "model": props.get("ro.product.model") or base["model"]}, kind=kind, sdk=int(sdk) if sdk.isdigit() else None,
                    connection=connection(serial, fields, kind))
    if props.get("sys.boot_completed") != "1":
        return dataclasses.replace(row, reason=f"{NOT_BOOTED[0]}: {serial} has not finished booting; {NOT_BOOTED[1]}")
    if kind == EMULATOR:
        avd = props.get("ro.boot.qemu.avd_name") or props.get("ro.kernel.qemu.avd_name") or ""
        return dataclasses.replace(row, key=f"emulator:{avd}") if avd else unstable(row, "the emulator names no AVD")
    serialno = props.get("ro.serialno", "")
    return dataclasses.replace(row, key=serialno) if serialno not in UNSET else unstable(row, f"ro.serialno is {serialno or 'blank'}")


def unstable(row: DeviceRow, why: str) -> DeviceRow:
    return dataclasses.replace(row, key=row.transport, note=f"unstable_id: {row.transport}: {why}; keyed by its transport serial, never resumed")


def deduplicated(rows: list[DeviceRow]) -> list[DeviceRow]:
    """Two ready transports with one key: neither key can be trusted."""
    counts = collections.Counter(row.key for row in rows if row.ready and row.note is None)
    return [unstable(row, f"{row.key} names {counts[row.key]} devices") if row.ready and row.note is None and counts[row.key] > 1 else row
            for row in rows]


def enumerate_devices(adb) -> list[DeviceRow]:
    """adb(*arguments) returns a finished process; a transport lost between the listing and its getprop is offline."""
    listed = adb("devices", "-l")
    if listed.returncode != 0:
        raise call_error(("devices", "-l"), listed)
    rows = []
    for serial, state, fields in transports(listed.stdout):
        props = None
        if state == READY:
            answer = adb("-s", serial, "shell", "getprop")
            props = properties(answer.stdout) if answer.returncode == 0 else None
        rows.append(classify(serial, state, fields, props))
    return deduplicated(rows)


COLUMNS = ("key", "alias", "kind", "model", "api", "connection", "state")


def listing(rows: list[DeviceRow], aliases: dict[str, str]) -> list[str]:
    """One table row per transport, then each reason and note as its own coded line."""
    by_key = {key: alias for alias, key in aliases.items()}
    table = [COLUMNS] + [(row.key, by_key.get(row.key, "-"), row.kind or "-", row.model or "-", str(row.sdk or "-"), row.connection or "-",
                          "ready" if row.ready else row.reason.split(":", 1)[0]) for row in rows]
    widths = [max(len(cells[i]) for cells in table) for i in range(len(COLUMNS))]
    ready = sum(row.ready for row in rows)
    lines = [f"devices:   {ready} ready, {len(rows) - ready} not ready"]
    lines += ["  " + "  ".join(cell.ljust(width) for cell, width in zip(cells, widths)).rstrip() for cells in table] if rows else []
    lines += [f"  {line}" for row in rows for line in (row.reason, row.note) if line]
    return lines
