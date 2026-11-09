"""dumpsys thermalservice as Android prints it: the HAL's current values first, the cached callback values when they are all there is."""

from device import thermal  # noqa: E402

CACHED_ONLY = """IsStatusOverride: false
Thermal Status: 0
Cached temperatures:
\tTemperature{mValue=33.25, mType=0, mName=cpu0, mStatus=0}
\tTemperature{mValue=-3.4028235E38, mType=3, mName=VIRTUAL-SKIN, mStatus=0}
\tTemperature{mValue=NaN, mType=1, mName=gpu, mStatus=0}
HAL Ready: false
"""


def test_the_hal_section_wins_and_sentinels_are_no_reading():
    text = CACHED_ONLY.replace("HAL Ready: false\n", "HAL Ready: true\nCurrent temperatures from HAL:\n\tTemperature{mValue=36.0, mType=0, mName=cpu0, mStatus=0}\n")
    reading = thermal.parse(text)
    assert (reading.sensors, reading.status, reading.source) == ({"cpu0": 36.0}, 0, "hal")


def test_only_cached_values_are_used_and_marked_cached():
    reading = thermal.parse(CACHED_ONLY)
    assert (reading.sensors, reading.source, reading.hottest) == ({"cpu0": 33.25}, "cached", 33.25)


def test_no_sensor_is_null_with_a_reason():
    reading = thermal.parse("Thermal Status: 2\n")
    assert reading.sensors is None and reading.status == 2 and reading.reason.startswith("no_temperatures:")
