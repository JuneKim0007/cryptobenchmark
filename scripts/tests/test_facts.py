import pathlib, sys, zipfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import facts


class FakeDevice:
    def __init__(self, su_output):
        self.su_output = su_output

    def run(self, *arguments, check=True):
        return type("Result", (), {"stdout": self.su_output})()


def test_pinning_needs_the_library_for_the_device_abi(tmp_path):
    apk = tmp_path / "app.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr(f"lib/arm64-v8a/{facts.NATIVE_LIBRARY}", b"")
    assert facts.pinning(apk, "arm64-v8a") is True
    assert facts.pinning(apk, "x86_64") is False
    assert facts.pinning(tmp_path / "missing.apk", "arm64-v8a") is False


def test_root_is_only_a_uid_zero_answer():
    assert facts.rooted(FakeDevice("uid=0(root) gid=0(root)")) is True
    assert facts.rooted(FakeDevice("/system/bin/sh: su: inaccessible or not found")) is False
