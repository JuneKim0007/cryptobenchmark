"""primitives.tsv: one line per primitive, input sizes as columns, statuses from screen.json, read back exactly."""
from dataclasses import replace

import pytest
from helpers import row, summary

from perfrepair.data_handler.inbound.primitives import read_primitives
from perfrepair.dto import Measurements
from perfrepair.dto.primitives import PrimitivesTable, rounded
from perfrepair.files import write_text
from perfrepair.result.primitives import build_table
from perfrepair.validation.primitives import validate_primitives

ROWS = [row("a64", "P1", input_size=64), row("a1k", "P1", input_size=1024), row("b64", "P2", input_size=64),
        row("d64", "P3", algorithm="ALG-D", input_size=64), row("g", "P1", operation="GEN", input_size=None, key_size=None)]
M = {"a64": {"timeNs": summary(100), "allocationCount": summary(3)}, "a1k": {"timeNs": replace(summary(912.345), cv=0.04)},
     "b64": {"timeNs": summary(80)}, "d64": {"timeNs": summary(50), "energyJ": replace(summary(0.0000123456), kind="estimated")},
     "g": {"timeNs": summary(123456.7, n=7)}}
STATUS = {"TypeA|ALG-A|P1": "accepted", "TypeA|ALG-A|P2": "accepted", "TypeA|ALG-D|P3": "broken"}
TABLE = build_table(ROWS, M, STATUS)


def _line(algorithm, provider, operation="OP1"):
    return next(x for x in TABLE.lines if (x.algorithm, x.provider, x.operation) == (algorithm, provider, operation))


def test_one_line_per_primitive_with_a_column_per_metric_and_input_size():
    assert TABLE.columns == ("timeNs@64", "timeNs@1024", "timeNs@-", "allocationCount@64", "energyJ@64")
    assert TABLE.metrics == ("timeNs", "allocationCount", "energyJ") and len(TABLE.lines) == 4
    a = _line("ALG-A", "P1")
    assert a.medians == {"timeNs@64": 100, "timeNs@1024": 912.3, "timeNs@-": None, "allocationCount@64": 3, "energyJ@64": None}
    assert a.cv == {"timeNs": 0.04, "allocationCount": 0.01, "energyJ": None}
    assert a.n == {"timeNs": 50, "allocationCount": 50, "energyJ": None}


def test_n_is_per_metric_so_one_energy_window_does_not_hide_fifty_timings():
    table = build_table([row("e", "P1", input_size=64)], {"e": {"timeNs": summary(9), "energyJ": summary(1, n=1)}},
                        {"TypeA|ALG-A|P1": "accepted"})
    assert table.lines[0].n == {"timeNs": 50, "energyJ": 1}


def test_a_deprecated_primitive_keeps_its_line_and_status():
    d = _line("ALG-D", "P3")
    assert d.status == "broken" and d.medians["energyJ@64"] == rounded(0.0000123456)


def test_the_text_form_reads_back_equal_and_is_compact(tmp_path):
    text = TABLE.to_tsv()
    lines = text.splitlines()
    assert lines[0] == "#schemaVersion\t2"
    assert lines[1].split("\t")[:7] == ["type", "algorithm", "provider", "operation", "keySize", "phase", "status"]
    assert lines[1].split("\t")[-6:] == ["timeNs.n", "allocationCount.n", "energyJ.n", "timeNs.cv", "allocationCount.cv",
                                          "energyJ.cv"]
    assert "TypeA\tALG-A\tP1\tGEN\t-\tWARM\taccepted\t-\t-\t123500\t-\t-\t7\t-\t-\t0.01\t-\t-" in lines
    assert "1.235e-05" in text
    write_text(tmp_path / "primitives.tsv", text)
    assert read_primitives(tmp_path) == TABLE


def test_another_schema_is_refused():
    with pytest.raises(ValueError, match="schemaVersion"):
        PrimitivesTable.from_tsv(TABLE.to_tsv().replace("#schemaVersion\t2", "#schemaVersion\t1"))


def test_the_validator_accepts_the_table_and_names_an_edited_line():
    measurements = Measurements({}, [], M)
    assert validate_primitives(PrimitivesTable.from_tsv(TABLE.to_tsv()), ROWS, measurements, STATUS) == []
    edited = TABLE.to_tsv().replace("\tbroken\t", "\tsomething\t")
    problems = validate_primitives(PrimitivesTable.from_tsv(edited), ROWS, measurements, STATUS)
    assert "status 'something' is not in" in problems[0]
    assert any("not the line" in p for p in problems) and any("missing" in p for p in problems)


def test_a_row_without_a_screen_verdict_is_refused():
    with pytest.raises(ValueError, match="primitive_not_screened"):
        build_table(ROWS, M, {k: v for k, v in STATUS.items() if "ALG-D" not in k})
