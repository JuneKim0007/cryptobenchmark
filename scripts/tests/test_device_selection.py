import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from device import selection_error  # noqa: E402

ONE = "List of devices attached\nemulator-5554\tdevice\n\n"
TWO = "* daemon started successfully\nList of devices attached\nemulator-5554\tdevice\n4A1B\toffline\n\n"
NONE = "List of devices attached\n\n"


def test_one_device_needs_no_selection():
    assert selection_error(ONE, None) is None


def test_several_without_a_selection_stop_with_one_coded_line():
    assert selection_error(TWO, None) == "several_devices: emulator-5554, 4A1B; set ANDROID_SERIAL to one"


def test_an_empty_serial_is_no_selection():
    assert selection_error(TWO, "").startswith("several_devices:")


def test_a_selected_attached_serial_passes():
    assert selection_error(TWO, "4A1B") is None


def test_a_selected_serial_not_attached_is_refused():
    assert selection_error(ONE, "4A1B") == "device_not_attached: ANDROID_SERIAL=4A1B; attached: emulator-5554"
    assert selection_error(NONE, "4A1B") == "device_not_attached: ANDROID_SERIAL=4A1B; attached: none"


def test_no_device_is_left_to_the_state_check():
    assert selection_error(NONE, None) is None
