import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from device.adb import PACKAGE, directories  # noqa: E402


def test_from_api_29_plan_and_output_share_the_media_directory():
    for sdk in (29, 30, 36):
        assert directories(sdk) == (f"/sdcard/Android/media/{PACKAGE}/cryptobench", f"/sdcard/Android/media/{PACKAGE}")


def test_below_api_29_plan_is_in_external_files_and_output_in_external_cache():
    assert directories(26) == (f"/sdcard/Android/data/{PACKAGE}/files/cryptobench", f"/sdcard/Android/data/{PACKAGE}/cache")
