import json
import os
from pathlib import Path

import pytest

from perfrepair.app.__main__ import main
from perfrepair.app.constants import Constants
from perfrepair.app.dependencies import bundled, read_libraries, registrations
from perfrepair.app.detect import detect
from perfrepair.app.gate import GateError, open_app, open_apps
from perfrepair.app.imports import import_reason
from perfrepair.app.lexer import Code, literal
from perfrepair.dto.language import JAVA, KOTLIN
from perfrepair.app.resolve import resolve
from perfrepair.app.roots import project_roots
from perfrepair.app.scan import call_pattern, scan
from perfrepair.app.sdk import sdk_levels
from perfrepair.app.sources import GENERATED, MAIN, TEST, build_files, origin, source_files
from perfrepair.data_handler.inbound import manifest_file, read_manifest, read_probe_index
from perfrepair.dto import ProviderEntry

F = Path(__file__).parent / "fixtures"
APP = F / "app"
MANIFEST = F / "results" / "manifest.yaml"


@pytest.fixture
def run():
    manifest, base = read_manifest(MANIFEST)
    return manifest, read_probe_index(manifest_file(manifest, base, "probe"))


def _android(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "settings.gradle").write_text("")
    (root / "src" / "main" / "java").mkdir(parents=True)
    return root


def _sites(text: str, index, language=JAVA):
    return scan(Code.of(text, language), "A", MAIN, call_pattern(index.engine_types))


def test_gate_accepts_an_android_project():
    app = open_app(APP)
    assert app.path == APP.resolve() and app.files > 0


@pytest.mark.parametrize("make, reason", [
    (lambda r: r / "missing", "not_a_directory"),
    (lambda r: r, "not_android_project"),
])
def test_gate_refuses_with_a_coded_reason(tmp_path, make, reason):
    with pytest.raises(GateError) as e:
        open_app(make(tmp_path))
    assert e.value.reason == reason


def test_gate_needs_a_manifest_or_a_source_set(tmp_path):
    (tmp_path / "build.gradle").write_text("")
    with pytest.raises(GateError, match="not_android_project"):
        open_app(tmp_path)
    (tmp_path / "AndroidManifest.xml").write_text("<manifest/>")
    assert open_app(tmp_path).files == 2


def test_gate_refuses_a_symlink_out_of_the_root(tmp_path):
    root = _android(tmp_path / "app")
    os.symlink(tmp_path, root / "src" / "main" / "java" / "out")
    with pytest.raises(GateError) as e:
        open_app(root)
    assert e.value.reason == "escapes_root"


def test_roots_top_level_is_the_folder_itself(tmp_path):
    _android(tmp_path / "app")
    (tmp_path / "app" / "lib").mkdir()
    (tmp_path / "app" / "lib" / "settings.gradle").write_text("")
    assert project_roots(tmp_path / "app") == ["."]
    (tmp_path / "bare" / "mod").mkdir(parents=True)
    (tmp_path / "bare" / "build.gradle").write_text("")
    _android(tmp_path / "bare" / "mod")
    assert project_roots(tmp_path / "bare") == ["."]


def test_roots_nested_and_several(tmp_path):
    _android(tmp_path / "one")
    (tmp_path / "deep" / "two" / "src" / "main" / "kotlin").mkdir(parents=True)
    (tmp_path / "deep" / "two" / "build.gradle.kts").write_text("")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "build.gradle").write_text("")
    _android(tmp_path / "build" / "skipped")
    assert project_roots(tmp_path) == ["deep/two", "one"]
    assert [a.projectRoot for a in open_apps(tmp_path)] == ["deep/two", "one"]


def test_roots_stop_at_the_depth_bound(tmp_path):
    _android(tmp_path / "a" / "b" / "c" / "d" / "e")
    assert project_roots(tmp_path) == []
    assert project_roots(tmp_path / "a") == ["b/c/d/e"]


def test_no_root_is_not_an_android_project(tmp_path):
    (tmp_path / "web" / "src").mkdir(parents=True)
    (tmp_path / "web" / "package.json").write_text("{}")
    with pytest.raises(GateError) as e:
        open_apps(tmp_path)
    assert e.value.reason == "not_android_project"


def test_roots_never_follow_a_symlink_out_of_the_folder(tmp_path):
    _android(tmp_path / "outside")
    (tmp_path / "app").mkdir()
    os.symlink(tmp_path / "outside", tmp_path / "app" / "android")
    with pytest.raises(GateError) as e:
        open_apps(tmp_path / "app")
    assert e.value.reason == "escapes_root"


def test_command_writes_one_unit_per_root(tmp_path, capsys):
    src = tmp_path / "src"
    for rel in ("android", "android_donation"):
        _android(src / rel)
        (src / rel / "src" / "main" / "java" / "A.java").write_text(
            "import javax.crypto.Cipher;\nclass A { void f() { Cipher.getInstance(\"AES\"); } }\n")
    assert main(["--manifest", str(MANIFEST), "--app", str(src), "--run", str(tmp_path / "run"), "--name", "x"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 2
    for unit, rel in (("x.android", "android"), ("x.android_donation", "android_donation")):
        out = tmp_path / "run" / "apps" / unit
        assert json.loads((out / "app.json").read_text())["projectRoot"] == rel
        assert json.loads((out / "scopes.json").read_text())["app"] == unit


def test_gate_caps_size(tmp_path):
    root = _android(tmp_path)
    (root / "src" / "main" / "java" / "A.java").write_text("x" * 100)
    with pytest.raises(GateError) as e:
        open_app(root, max_source_bytes=50)
    assert e.value.reason == "too_large"


def test_sources_are_tagged_and_ignored_folders_skipped():
    tags = {f.rel: f.origin for f in source_files(APP)}
    assert tags["src/test/java/demo/CryptoTest.java"] == TEST
    assert tags["src/main/kotlin/demo/Vault.kt"] == MAIN
    assert not any(r.startswith("build/") for r in tags)
    assert origin(Path("app/src/androidTest/java/A.kt")) == TEST
    assert origin(Path("app/src/sharedTest/java/A.kt")) == TEST
    assert origin(Path("app/src/generated/java/A.java")) == GENERATED


def test_lexer_masks_comments_strings_and_nested_kotlin_comments():
    code = Code.of('/* a /* b */ c */ val s = "x}" // d\n', KOTLIN)
    assert code.masked.strip().startswith("val s =") and "}" not in code.masked
    assert literal('"AES/$m"', KOTLIN) is None and literal('"AES/$m"', JAVA) == "AES/$m"
    assert literal('"""raw"""', KOTLIN) == "raw"


def test_calls_inside_comments_and_strings_are_not_sites(run):
    sites = _sites('class A {\n'
                   '  // Object a = Cipher.getInstance("AES/GCM/NoPadding");\n'
                   '  /* Object b = Mac.getInstance("HmacSHA256"); */\n'
                   '  String s = "Mac.getInstance(x)"; Object c = Mac.getInstance("HmacSHA256");\n'
                   '}\n', run[1])
    assert [(s.engineType, s.line) for s in sites] == [("Mac", 4)]


def test_a_call_split_across_lines_keeps_its_exact_text(run):
    [site] = _sites('val c = Cipher\n    .getInstance(\n  "AES/GCM/NoPadding",\n "Fast")\n', run[1], KOTLIN)
    assert site.line == 1 and site.algorithm.literal == "AES/GCM/NoPadding" and site.provider.literal == "Fast"
    assert site.call == 'Cipher\n    .getInstance(\n  "AES/GCM/NoPadding",\n "Fast")'


@pytest.mark.parametrize("text, reason", [
    ("import javax.crypto.Cipher;\n", None),
    ("import javax.crypto.*;\n", None),
    ("import com.other.Cipher;\n", "other_import"),
    ("import javax.crypto.Cipher as C\n", "not_imported"),
    ("class Cipher {}\nimport javax.crypto.*;\n", "local_declaration"),
    ("", "not_imported"),
])
def test_import_decides_whether_the_type_is_the_platform_class(text, reason):
    code = Code.of(text + "x = Cipher.getInstance(a)", KOTLIN)
    assert import_reason(code, "Cipher", code.masked.index("Cipher.get")) == reason


def test_fully_qualified_names_need_no_import():
    code = Code.of("x = javax.crypto.Cipher.getInstance(a); y = other.Cipher.getInstance(a)", JAVA)
    first, second = (i for i in range(len(code.text)) if code.text.startswith("Cipher.get", i))
    assert import_reason(code, "Cipher", first) is None
    assert import_reason(code, "Cipher", second) == "other_qualifier"


def test_constants_fold_java_and_kotlin():
    java = Constants(Code.of('class A { private static final String M = "GCM";\n'
                             'static final String T = "AES/" + M + "/NoPadding"; String inst = "x"; }', JAVA))
    assert java.fold("T") == "AES/GCM/NoPadding" and java.fold("inst") is None and java.fold("A.T") == java.fold("T")
    kotlin = Constants(Code.of('const val A = "x"\nval B = A + "y"\nobject O { val C = "z" }\n'
                               'class K { val D = "w"\n fun f() { val E = "v" } }\n'
                               'val T = "$A"\n', KOTLIN))
    assert (kotlin.fold("B"), kotlin.fold("O.C"), kotlin.fold("D"), kotlin.fold("E"), kotlin.fold("T")) == \
        ("xy", "z", None, None, None)


def test_a_name_declared_twice_is_not_folded():
    c = Constants(Code.of('class A { static final String X = "a"; void f() { String X = "b"; } }', JAVA))
    assert c.fold("X") is None


def test_bundled_libraries_come_from_the_data_list():
    found = bundled(build_files(APP), read_libraries())
    assert [(b.artifact, b.providerName) for b in found] == [
        ("com.google.crypto.tink:tink-android", None), ("org.bouncycastle:bcprov-jdk18on", "BC")]


def test_provider_registrations_need_the_platform_class():
    code = Code.of("import java.security.Security\nfun f() { Security.addProvider(P())\n"
                   "other.Security.addProvider(Q()) }", True)
    assert [(r.line, r.expr) for r in registrations(code, "A.kt")] == [(2, "P()")]


def test_sdk_levels_resolve_literals_and_named_properties(tmp_path):
    assert sdk_levels(build_files(APP)) == {"minSdk": 24, "targetSdk": 34}
    (tmp_path / "build.gradle.kts").write_text('plugins { id("com.android.application") }\n'
                                               'android { defaultConfig { minSdk = libs.versions.min.sdk.get().toInt()\n'
                                               'targetSdk = Versions.unknown } }')
    (tmp_path / "libs.versions.toml").write_text('[versions]\nmin-sdk = "26"\n')
    assert sdk_levels(build_files(tmp_path)) == {"minSdk": 26, "targetSdk": None}


def test_detect_drops_import_less_sites_and_skips_tests(run):
    manifest, index = run
    found = detect(open_app(APP), index, manifest.providers)
    files = {s["file"] for s in found.sites}
    assert "src/test/java/demo/CryptoTest.java" not in files and found.testFiles == 1
    assert [(d["file"], d["reason"]) for d in found.dropped] == [("src/main/java/demo/Shadow.java", "not_imported")]
    assert found.folded == 5


def test_resolution_per_site(run):
    manifest, index = run
    crypto = [s for s in detect(open_app(APP), index, manifest.providers).sites if s["file"].endswith("Crypto.java")]
    assert [(s["line"], s["resolvedProvider"], s["resolvedAlgorithm"], s["resolution"]) for s in crypto] == [
        (12, "Slow", "AES/GCM/NoPadding", "explicit"), (17, "Fast", "SHA-256", "default"),
        (21, "Fast", "AES/GCM/NoPadding", "explicit"), (25, None, None, "unresolved_provider"),
        (31, "Bundled", "AES/GCM/NoPadding", "provider_not_on_device")]


def test_default_resolution_follows_manifest_precedence(run):
    manifest, index = run
    cipher, mac = _sites('Object c = Cipher.getInstance("aes/gcm/nopadding"); Object m = Mac.getInstance("HmacSHA256");',
                         index)
    flipped = [ProviderEntry("Slow", 1, 2), ProviderEntry("Fast", 2, 2)]
    assert resolve(cipher, index, manifest.providers)["resolvedProvider"] == "Fast"
    assert resolve(cipher, index, flipped)["resolvedProvider"] == "Slow"
    assert resolve(mac, index, manifest.providers)["resolvedProvider"] == "Slow"
    assert resolve(cipher, index, manifest.providers)["resolvedAlgorithm"] == "AES/GCM/NoPadding"


def test_command_writes_the_app_folder(tmp_path, capsys):
    assert main(["--manifest", str(MANIFEST), "--app", str(APP), "--run", str(tmp_path), "--name", "demo"]) == 0
    out = tmp_path / "apps" / "demo"
    docs = {n: json.loads((out / f"{n}.json").read_text()) for n in ("sites", "app", "scopes")}
    assert len(docs["sites"]["sites"]) == 12 and len(docs["scopes"]["scopes"]) == 11
    assert docs["app"]["projectRoot"] == "." and docs["app"]["minSdk"] == 24 and docs["app"]["registers"][0]["expr"] == "new BundledProvider()"
    assert "1 dropped by import" in capsys.readouterr().out


def test_command_refuses_a_gate_failure_and_a_path_name(tmp_path, capsys):
    assert main(["--manifest", str(MANIFEST), "--app", str(tmp_path), "--run", str(tmp_path), "--name", "x"]) == 2
    assert "not_android_project" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["--manifest", str(MANIFEST), "--app", str(APP), "--run", str(tmp_path), "--name", "../x"])


def test_an_argument_next_to_a_comment_is_still_a_literal(run):
    [site] = _sites('Object c = Cipher.getInstance(\n  "AES/GCM/NoPadding", // why\n  /* who */ "Fast");\n', run[1])
    assert (site.algorithm.expr, site.provider.expr) == ('"AES/GCM/NoPadding"', '"Fast"')
    assert (site.algorithm.literal, site.provider.literal) == ("AES/GCM/NoPadding", "Fast")


def test_a_kotlin_constant_with_a_trailing_comment_folds():
    assert Constants(Code.of('const val A = "x" // note\n', KOTLIN)).fold("A") == "x"


def test_one_expression_end_with_the_continuations_as_a_parameter():
    code = Code.of('val a = "x" +\n  "y"\nval b = 1\n', KOTLIN)
    assert code.text[8:code.expression_end(8, ("+",), ("+",))] == '"x" +\n  "y"'
    assert code.text[8:code.expression_end(8, (), ())] == '"x" +'
    java = Code.of('String a = "x"\n  + "y"; int b;', JAVA)
    assert java.text[10:java.expression_end(10, (), ())] == ' "x"\n  + "y"'
