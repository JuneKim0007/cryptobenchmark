"""Which build of the guide a device reads, and that a fallback is said once per provider."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stages import guide  # noqa: E402
from cryptobench.catalogue.provider_builds import provider_builds  # noqa: E402


def test_a_device_names_its_platform_and_a_host_its_jdk():
    assert guide.platform({"sdkInt": 37, "javaVersion": "0"}) == "android-37"
    assert guide.platform({"javaVersion": "25.0.1"}) == "jdk-25"
    assert guide.platform({}) is None


def test_an_exact_build_wins_and_a_newer_device_takes_the_nearest_below():
    builds = provider_builds()
    assert builds.nearest("AndroidOpenSSL", "android-33", None) == ("AndroidOpenSSL @ android-33", True)
    assert builds.nearest("AndroidOpenSSL", "android-37", None) == ("AndroidOpenSSL @ android-36", False)
    assert builds.nearest("NoSuchProvider", "android-37", None) == (None, False)


def test_a_fallback_is_one_line_per_provider():
    item = {"build": "P @ android-36", "exactBuild": False}
    lines = guide.fallbacks({"items": {"P": {"Cipher": {"A": item, "B": item}}, "Q": {"Mac": {"M": {"build": "Q @ android-37", "exactBuild": True}}}}})
    assert lines == ["guide_build_fallback: P has no row of its own for this build; using P @ android-36"]
