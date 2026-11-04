import json
import pathlib
import shlex
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from stages import bundled  # noqa: E402

CONSCRYPT = {"artifact": "org.conscrypt:conscrypt-android:2.5.3", "create": "org.conscrypt.Conscrypt#newProvider"}


class Bundled(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.global_file = self.dir / "global.yaml"

    def write(self, text):
        self.global_file.write_text("schemaVersion: 1\nselection: {testSet: a.yaml}\n" + text)
        return bundled.read(self.global_file)

    def test_no_providers_section_builds_and_passes_nothing(self):
        shipped = self.write("")
        self.assertEqual([], shipped)
        self.assertEqual([], bundled.gradle_properties(shipped))
        self.assertEqual([], bundled.instrumentation_arguments(shipped))

    def test_artifacts_become_one_comma_separated_gradle_property(self):
        shipped = self.write("providers:\n  bundled:\n  - {artifact: 'a:b:1', create: a.B}\n  - {artifact: 'c:d:2', create: c.D, alias: null}\n")
        self.assertEqual(["-PbundledArtifacts=a:b:1,c:d:2"], bundled.gradle_properties(shipped))
        self.assertEqual({"artifact": "c:d:2", "create": "c.D"}, shipped[1])

    def test_the_instrumentation_argument_survives_the_device_shell(self):
        arguments = bundled.instrumentation_arguments([dict(CONSCRYPT, alias="Outer$Inner")])
        self.assertEqual(["-e", "bundledProviders"], arguments[:2])
        self.assertEqual({"bundledProviders": [dict(CONSCRYPT, alias="Outer$Inner")]}, json.loads(shlex.split(arguments[2])[0]))

    def test_a_malformed_list_is_refused(self):
        with self.assertRaisesRegex(bundled.BundledError, "wrong_type: providers.bundled"):
            self.write("providers: {bundled: [{create: a.B}]}\n")

    def test_effective_must_record_what_the_app_was_built_with(self):
        effective = self.dir / "effective.yaml"
        effective.write_text("bundledProviders:\n- {artifact: 'org.conscrypt:conscrypt-android:2.5.3', create: org.conscrypt.Conscrypt#newProvider}\n")
        bundled.check_effective(effective, [CONSCRYPT])
        with self.assertRaisesRegex(bundled.BundledError, "bundled_mismatch"):
            bundled.check_effective(effective, [])


if __name__ == "__main__":
    unittest.main()
