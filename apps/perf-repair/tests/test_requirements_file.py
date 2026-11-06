import pytest

from perfrepair.data_handler.inbound.probe import Requirements
from perfrepair.dto.coded import InputError

DOCUMENT = """
schemaVersion: 1
capturedAtMillis: 10
deviceClockMillis: 7
services:
- {provider: P, type: Cipher, algorithm: A, status: runnable, millis: 1}
"""


def test_the_requirements_of_a_capture_are_the_file_with_its_stamp(tmp_path):
    (tmp_path / "requirements_20260101T000000Z.yaml").write_text(DOCUMENT)
    found = Requirements.beside(tmp_path / "probe_20260101T000000Z.yaml")
    assert found.of("P", "Cipher", "A")["status"] == "runnable" and found.of("P", "Cipher", "B") is None


def test_another_schema_version_is_refused(tmp_path):
    path = tmp_path / "requirements_20260101T000000Z.yaml"
    path.write_text(DOCUMENT.replace("schemaVersion: 1", "schemaVersion: 2"))
    with pytest.raises(InputError):
        Requirements.load(path)
