import logging
import sys
from pathlib import Path

import pytest

from perfrepair.inputs.resolve import Candidate, InputError, Need, resolve
from perfrepair.inputs.table import SCREENING_CATALOG, Row
from perfrepair.log import attach
from perfrepair.log.stderr import Stderr


def read(path):
    return Path(path).read_text()


def test_an_explicit_value_is_loaded_and_not_logged(tmp_path, caplog):
    (tmp_path / "a").write_text("A")
    caplog.set_level(logging.INFO, "perfrepair")
    got = resolve("x", [Candidate(tmp_path / "a", "cli"), Candidate(tmp_path / "b", "packaged", explicit=False)],
                  read, Need.DEFAULT)
    assert (got.value, got.source) == ("A", "cli")
    assert caplog.records == []


def test_an_explicit_value_that_does_not_load_is_missing_file_never_a_fallback(tmp_path):
    (tmp_path / "b").write_text("B")
    with pytest.raises(InputError, match=r"^missing_file: x: .*/nope \(file f\.yaml x\)") as e:
        resolve("x", [Candidate(tmp_path / "nope", "file f.yaml x"), Candidate(tmp_path / "b", "packaged", False)],
                read, Need.DEFAULT)
    assert e.value.code == "missing_file"


def test_unset_values_fall_through_and_a_found_default_is_logged_once(tmp_path, caplog):
    (tmp_path / "b").write_text("B")
    caplog.set_level(logging.INFO, "perfrepair")
    got = resolve("x", [Candidate(None, "cli"), Candidate(None, "env X"),
                        Candidate(tmp_path / "b", "packaged x", explicit=False, note="(no settings)")], read, Need.DEFAULT)
    assert (got.value, got.source) == ("B", "packaged x")
    [r] = caplog.records
    assert (r.getMessage(), r.code, r.input, r.source) == ("x: packaged x (no settings)", "default", "x", "packaged x")


def test_an_unset_default_that_fails_falls_through_to_the_next(tmp_path):
    (tmp_path / "c").write_text("C")
    got = resolve("x", [Candidate(tmp_path / "gone", "d1", False), Candidate(tmp_path / "c", "d2", False)], read,
                  Need.DEFAULT)
    assert got.value == "C"


@pytest.mark.parametrize("need", [Need.REQUIRED, Need.DEFAULT])
def test_nothing_found_is_an_error_unless_optional(need):
    with pytest.raises(InputError, match=r"^missing_input: x: nothing found \(cli\)"):
        resolve("x", [Candidate(None, "cli")], read, need)


def test_nothing_found_for_an_optional_input_is_the_null_value_and_logged(caplog):
    caplog.set_level(logging.INFO, "perfrepair")
    got = resolve("x", [Candidate(None, "cli")], read, Need.OPTIONAL, null={})
    assert (got.value, got.source) == ({}, "none")
    assert [(r.code, r.getMessage()) for r in caplog.records] == [("not_found", "x: not found (cli); skipped")]


def test_a_policy_appends_its_packaged_default(tmp_path, caplog):
    (tmp_path / "p").write_text("P")
    caplog.set_level(logging.INFO, "perfrepair")
    policy = Row("y", need=Need.DEFAULT, packaged=tmp_path / "p", label="packaged y")
    assert policy.resolve([Candidate(None, "file")], read, note="(unset)").value == "P"
    assert caplog.messages == ["y: packaged y (unset)"]


def test_the_screening_catalog_row_names_its_setting_and_packaged_file():
    assert SCREENING_CATALOG.key == "device.screening.catalog"
    assert SCREENING_CATALOG.need is Need.DEFAULT and SCREENING_CATALOG.packaged.is_file()


def test_the_stderr_handler_is_attached_once_and_follows_a_replaced_stderr(capsys):
    logger = logging.getLogger("perfrepair")
    before = list(logger.handlers)
    logger.handlers[:] = []
    try:
        attach()
        attach()
        stderr = [h for h in logger.handlers if isinstance(h, Stderr)]
        assert len(stderr) == 1 and len(logger.handlers) == 2
        logging.getLogger("perfrepair.inputs").info("hello")
        logging.getLogger("perfrepair.inputs").debug("for the run log only")
        assert capsys.readouterr().err == "hello\n"
        assert stderr[0].stream is sys.stderr
    finally:
        logger.handlers[:] = before
