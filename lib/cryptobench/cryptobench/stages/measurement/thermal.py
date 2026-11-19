"""Device temperatures from `dumpsys thermalservice`, which an unrooted shell may read; sensors keep the names the thermal HAL gives them."""
import dataclasses, re

from cryptobench.shared.device import timeouts
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.errors.line import one_line

TEMPERATURE = re.compile(r"Temperature\{mValue=([^,]+), mType=(-?\d+), mName=([^,}]+), mStatus=-?\d+\}")
CPU_TYPE, SKIN_TYPE = 0, 3   # android.hardware.thermal TemperatureType.CPU, .SKIN
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

    def hottest_of(self, kind):
        """(name, Celsius) of the hottest sensor of a HAL type read live; None when there is none."""
        if self.source != LIVE or not self.sensors:
            return None
        found = [(celsius, name) for name, celsius in self.sensors.items() if (self.types or {}).get(name) == kind]
        return max(found)[::-1] if found else None

    @property
    def skin(self):
        return self.hottest_of(SKIN_TYPE)

    @property
    def cpu(self):
        return self.hottest_of(CPU_TYPE)


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


def extremes(starts, ends, when):
    """The gate's skin sensor, by name, and the CPU sensors: the hottest of each over the starts and the ends; None when neither was read."""
    fields = []
    for label, kind in (("skin", SKIN_TYPE), ("CPU", CPU_TYPE)):
        sides = [[found for r in side if (found := r.hottest_of(kind))] for side in (starts, ends)]
        if not all(sides):
            fields.append(f"{label} unavailable")
            continue
        named = f"{label} {'/'.join(sorted({name for side in sides for name, _ in side}))}" if kind == SKIN_TYPE else label
        start, end = (max(c for _, c in side) for side in sides)
        fields.append(f"{named} {start:.1f} C {when[0]}, {end:.1f} C {when[1]}")
    return None if all(f.endswith(" unavailable") for f in fields) else "; ".join(fields)


def read(device):
    try:
        return parse(device.shell("dumpsys thermalservice"))
    except DeviceLost:
        raise
    except (DeviceError, timeouts.StepTimeout) as error:
        return Reading(None, None, None, "thermal_unavailable: " + one_line(error, 200))


def poll(device):
    """The skin sensors alone, for a wait that reads the phone every minute."""
    try:
        return parse(device.shell(SKIN_LINES))
    except DeviceLost:
        raise
    except (DeviceError, timeouts.StepTimeout) as error:
        return Reading(None, None, None, "thermal_unavailable: " + one_line(error, 200))


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
    except DeviceLost:
        raise
    except (DeviceError, timeouts.StepTimeout):
        return Capability(False, "probe_failed")
    return Capability(reason == "ok", reason, tuple(name for name, kind in (reading.types or {}).items() if kind == SKIN_TYPE))
