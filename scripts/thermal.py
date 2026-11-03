"""Device temperatures from `dumpsys thermalservice`, which an unrooted shell may read; sensors keep the names the thermal HAL gives them."""
import dataclasses, re

import timeouts
from device import DeviceError

TEMPERATURE = re.compile(r"Temperature\{mValue=([^,]+), mType=-?\d+, mName=([^,}]+), mStatus=-?\d+\}")
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

    @property
    def hottest(self):
        return max(self.sensors.values()) if self.sensors else None


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
        sensors = {name.strip(): value for raw, name in TEMPERATURE.findall(section(text, header)) if (value := celsius(raw)) is not None}
        if sensors:
            return Reading(sensors, status, source)
    return Reading(None, status, None, "no_temperatures: dumpsys thermalservice listed no sensor with a reading")


def read(device):
    try:
        return parse(device.shell("dumpsys thermalservice"))
    except (DeviceError, timeouts.StepTimeout) as error:
        return Reading(None, None, None, "thermal_unavailable: " + " ".join(str(error).split())[:200])
