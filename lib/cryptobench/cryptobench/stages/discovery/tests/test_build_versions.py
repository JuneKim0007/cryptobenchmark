import types

from cryptobench.stages.discovery import build_versions

LISTING = """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<apex-info-list>
<apex-info moduleName="com.android.conscrypt" modulePath="/system/apex/com.google.android.conscrypt.apex" versionCode="351010000" isFactory="true" isActive="false"/>
<apex-info moduleName="com.android.conscrypt" modulePath="/data/apex/active/com.google.android.conscrypt@360910000.apex" versionCode="360910000" isFactory="false" isActive="true"/>
<apex-info moduleName="com.android.art" modulePath="/system/apex/com.google.android.art.apex" versionCode="361011000" isFactory="true" isActive="true"/>
<apex-info moduleName="com.android.tzdata" versionCode="9" isActive="true"/>
</apex-info-list>
"""


class Device:
    def __init__(self, answers):
        self.answers = answers

    def run(self, *arguments, check=True):
        code, out = self.answers.get(arguments[1].split()[-1], (1, ""))
        return types.SimpleNamespace(returncode=code, stdout=out, stderr="")


def test_the_active_conscrypt_and_art_versions_and_the_patch_are_read():
    device = Device({build_versions.SECURITY_PATCH: (0, "2026-10-05\n"), str(build_versions.paths.DeviceDirs.APEX_INFO): (0, LISTING)})
    assert build_versions.read(device, 36) == {"securityPatch": "2026-10-05", "apex": {"com.android.conscrypt": 360910000, "com.android.art": 361011000}}


def test_a_module_the_device_lacks_is_null_without_a_warning(capsys):
    listing = LISTING.replace("com.android.art", "com.android.runtime")
    assert build_versions.apex(Device({str(build_versions.paths.DeviceDirs.APEX_INFO): (0, listing)}), 36)["com.android.art"] is None
    assert capsys.readouterr().out == ""


def test_an_unreadable_list_and_an_empty_patch_are_null_with_one_coded_line_each(capsys):
    assert build_versions.read(Device({build_versions.SECURITY_PATCH: (0, "\n")}), 36) == {"securityPatch": None, "apex": None}
    assert capsys.readouterr().out.splitlines() == [
        f"warning: facts_unknown: build.securityPatch: getprop {build_versions.SECURITY_PATCH} printed nothing; facts.yaml records null",
        f"warning: facts_unknown: build.apex: neither {build_versions.paths.DeviceDirs.APEX_INFO} nor '{build_versions.PM_APEX}' names an active module; "
        "facts.yaml records null"]


def test_without_the_list_the_package_manager_gives_the_versions_as_on_android_10(capsys):
    listed = "package:com.android.tzdata versionCode:290000000\npackage:com.android.conscrypt versionCode:291900000\npackage:com.android.runtime.release versionCode:290000000\n"
    device = Device({build_versions.SECURITY_PATCH: (0, "2020-02-05\n"), str(build_versions.paths.DeviceDirs.APEX_INFO): (1, ""),
                     build_versions.PM_APEX.split()[-1]: (0, listed)})
    assert build_versions.read(device, 29) == {"securityPatch": "2020-02-05", "apex": {"com.android.conscrypt": 291900000, "com.android.art": None}}
    assert capsys.readouterr().out == ""


def test_the_list_wins_over_the_package_manager_when_it_names_a_module():
    device = Device({str(build_versions.paths.DeviceDirs.APEX_INFO): (0, LISTING), build_versions.PM_APEX.split()[-1]: (0, "package:com.android.conscrypt versionCode:1\n")})
    assert build_versions.apex(device, 36)["com.android.conscrypt"] == 360910000


def test_below_sdk_29_every_module_is_absent_without_reading_the_list(capsys):
    device = Device({build_versions.SECURITY_PATCH: (0, "2018-08-05\n")})
    assert build_versions.read(device, 28) == {"securityPatch": "2018-08-05", "apex": {"com.android.conscrypt": None, "com.android.art": None}}
    assert capsys.readouterr().out == ""
