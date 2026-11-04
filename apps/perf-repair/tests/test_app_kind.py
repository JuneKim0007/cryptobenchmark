"""app/facts/kind.py: app, library, unknown_layout or not_android from build files and manifests; fixtures in tmp_path."""
import pytest
from perfrepair.app.facts.kind import (
    APP,
    CONVENTION_PLUGIN,
    LEGACY_ANT,
    LIBRARY,
    MANIFEST_ONLY,
    NO_ANDROID_PLUGIN,
    NOT_ANDROID,
    UNKNOWN_LAYOUT,
    android_kind,
)

CATALOG = """[versions]
agp = "8.5.0"

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
android_library = "com.android.library:8.5.0"
kotlin-android = { id = "org.jetbrains.kotlin.android", version = "2.0.0" }
"""


def tree(root, files):
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


@pytest.mark.parametrize("name,text", [
    ("build.gradle", "plugins {\n    id 'com.android.application'\n}\nandroid { defaultConfig { applicationId 'x.groovy' } }\n"),
    ("build.gradle.kts", 'plugins {\n    id("com.android.application")\n}\nandroid { defaultConfig { applicationId = "x.kts" } }\n'),
    ("build.gradle", "apply plugin: 'com.android.application'\nandroid { defaultConfig { applicationId \"x.apply\" } }\n"),
])
def test_a_module_applying_the_application_plugin_is_an_app_with_its_id(tmp_path, name, text):
    tree(tmp_path, {"settings.gradle": "include ':app'\n", f"app/{name}": text})
    got = android_kind(tmp_path)
    assert got.kind == APP and got.reason is None and got.applicationId.startswith("x.")


def test_a_version_catalog_alias_resolves_through_the_plugins_table(tmp_path):
    tree(tmp_path, {"gradle/libs.versions.toml": CATALOG, "app/build.gradle.kts":
                    "plugins {\n    alias(libs.plugins.android.application)\n    alias(libs.plugins.kotlin.android)\n}\n",
                    "app/src/main/AndroidManifest.xml": '<manifest package="from.manifest" />'})
    got = android_kind(tmp_path)
    assert (got.kind, got.applicationId) == (APP, "from.manifest")


@pytest.mark.parametrize("files", [
    {"lib/build.gradle": "plugins { id 'com.android.library' }\n"},
    {"lib/build.gradle.kts": 'plugins { id("com.android.library") }\n'},
    {"lib/build.gradle": "apply plugin: 'com.android.library'\n"},
    {"gradle/libs.versions.toml": CATALOG, "lib/build.gradle.kts": "plugins { alias(libs.plugins.android.library) }\n"},
])
def test_library_forms_are_a_library(tmp_path, files):
    assert android_kind(tree(tmp_path, files)).kind == LIBRARY


def test_one_application_module_among_libraries_makes_the_tree_an_app(tmp_path):
    tree(tmp_path, {"lib/build.gradle": "apply plugin: 'com.android.library'\n",
                    "app/build.gradle": "apply plugin: 'com.android.application'\n"})
    assert android_kind(tmp_path).kind == APP


def test_a_commented_out_plugin_is_not_applied(tmp_path):
    tree(tmp_path, {"build.gradle": "// apply plugin: 'com.android.application'\napply plugin: 'com.android.library'\n"})
    assert android_kind(tmp_path).kind == LIBRARY


def test_legacy_ant_app_and_library(tmp_path):
    app = tree(tmp_path / "a", {"AndroidManifest.xml": '<manifest package="legacy.app" >\n</manifest>',
                                "project.properties": "target=android-19\n", "src/x/A.java": "class A {}"})
    lib = tree(tmp_path / "l", {"AndroidManifest.xml": "<manifest/>", "project.properties": "android.library=true\n"})
    assert (android_kind(app).kind, android_kind(app).reason, android_kind(app).applicationId) == (APP, LEGACY_ANT, "legacy.app")
    assert (android_kind(lib).kind, android_kind(lib).reason) == (LIBRARY, LEGACY_ANT)


def test_a_readme_folder_is_not_android_and_a_lone_manifest_is_an_unknown_layout(tmp_path):
    readme = tree(tmp_path / "r", {"README.md": "x", "main_commit_data.csv": "a,b"})
    manifest = tree(tmp_path / "m", {"AndroidManifest.xml": "<manifest/>", "src/x/A.java": "class A {}"})
    assert android_kind(readme).kind == NOT_ANDROID and android_kind(tmp_path / "absent").kind == NOT_ANDROID
    assert (android_kind(manifest).kind, android_kind(manifest).reason) == (UNKNOWN_LAYOUT, MANIFEST_ONLY)


def test_a_convention_plugin_is_an_unknown_layout_with_its_reason(tmp_path):
    tree(tmp_path, {"app/build.gradle.kts": 'plugins {\n    id("my.android.application")\n}\n',
                    "build-logic/src/main/kotlin/A.kt": "class A"})
    assert (android_kind(tmp_path).kind, android_kind(tmp_path).reason) == (UNKNOWN_LAYOUT, CONVENTION_PLUGIN)


def test_gradle_files_without_an_android_plugin_beside_a_manifest(tmp_path):
    tree(tmp_path, {"build.gradle": "apply plugin: 'android'\n", "src/main/AndroidManifest.xml": "<manifest/>"})
    assert (android_kind(tmp_path).kind, android_kind(tmp_path).reason) == (UNKNOWN_LAYOUT, NO_ANDROID_PLUGIN)
