"""Device temperatures from `dumpsys thermalservice`, which an unrooted shell may read; sensors keep the names the thermal HAL gives them."""
import dataclasses, re

import timeouts
from device.adb import DeviceError

TEMPERATURE = re.compile(r"Temperature\{mValue=([^,]+), mType=(-?\d+), mName=([^,}]+), mStatus=-?\d+\}")
SKIN_TYPE = 3   # android.hardware.thermal TemperatureType.SKIN
SIMULATED_HARDWARE = ("ranchu", "goldfish")
LIVE = "hal"
# only the headers and the skin lines cross adb; parse() still tells the live section from the cached one
SKIN_LINES = "dumpsys thermalservice | grep -E '^(Thermal Status|Cached temperatures|Current temperatures from HAL)|mType=3'"
STATUS = re.compile(r"^\s*Thermal Status: (-?\d+)\s*$", re.M)
# "Current temperatures from HAL" is queried when dumpsys runs; "Cached temperatures" holds the HAL's last callback, possibly old.
SECTIONS = (("hal", "Current temperatures from HAL:"), ("cached", "Cached temperatures:"))
# The HAL reports an unknown value as -Float.MAX_VALUE (-3.4e38); anything outside this range is no reading.
PLAUSIBLE = (-60.0, 200.0)


@dataclasses.dataclass(frozen=True)
class Reading:
    sensors: dict | None
    status: int | None
    source: str | None = None
    reason: str | None = None
    types: dict | None = None

    @property
    def hottest(self):
        return max(self.sensors.values()) if self.sensors else None

    @property
    def skin(self):
        """(name, Celsius) of the hottest skin-type sensor read live from the HAL; None when there is none."""
        if self.source != LIVE or not self.sensors:
            return None
        found = [(celsius, name) for name, celsius in self.sensors.items() if (self.types or {}).get(name) == SKIN_TYPE]
        return max(found)[::-1] if found else None


@dataclasses.dataclass(frozen=True)
class Capability:
    """Decided once at startup: later code reads this and never decides availability again."""
    available: bool
    reason: str
    sensors: tuple = ()


def celsius(text):
    try:
        value = float(text)
    except ValueError:
        return None
    return value if PLAUSIBLE[0] <= value <= PLAUSIBLE[1] else None


def section(text, header):
    """The indented lines under a header line, up to the next line that is not indented."""
    lines, inside = [], False
    for line in text.splitlines():
        if line.strip() == header:
            inside = True
        elif inside and line[:1].isspace():
            lines.append(line)
        elif inside:
            break
    return "\n".join(lines)


def parse(text):
    found = STATUS.search(text)
    status = int(found.group(1)) if found else None
    for source, header in SECTIONS:
        found = [(name.strip(), value, int(kind)) for raw, kind, name in TEMPERATURE.findall(section(text, header)) if (value := celsius(raw)) is not None]
        if found:
            return Reading({name: value for name, value, _ in found}, status, source, types={name: kind for name, _, kind in found})
    return Reading(None, status, None, "no_temperatures: dumpsys thermalservice listed no sensor with a reading")


def read(device):
    try:
        return parse(device.shell("dumpsys thermalservice"))
    except (DeviceError, timeouts.StepTimeout) as error:
        return Reading(None, None, None, "thermal_unavailable: " + " ".join(str(error).split())[:200])


def poll(device):
    """The skin sensors alone, for a wait that reads the phone every minute."""
    try:
        return parse(device.shell(SKIN_LINES))
    except (DeviceError, timeouts.StepTimeout) as error:
        return Reading(None, None, None, "thermal_unavailable: " + " ".join(str(error).split())[:200])


def judged(text):
    """Why a full dump gives no live skin reading; ok when it does."""
    reading = parse(text)
    if not text.strip() or "Can't find service" in text:
        return "no_thermal_service", reading
    if "HAL Ready: false" in text:
        return "hal_not_ready", reading
    if reading.sensors is None:
        return "no_temperatures", reading
    if reading.source != LIVE:
        return "cached_only", reading
    return ("ok" if reading.skin else "no_skin_sensor"), reading


def capability(device):
    try:
        if device.shell("getprop ro.hardware").strip() in SIMULATED_HARDWARE:
            return Capability(False, "simulated_device")
        reason, reading = judged(device.shell("dumpsys thermalservice"))
    except (DeviceError, timeouts.StepTimeout):
        return Capability(False, "probe_failed")
    return Capability(reason == "ok", reason, tuple(name for name, kind in (reading.types or {}).items() if kind == SKIN_TYPE))
