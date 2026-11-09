"""The primitives stage: rows, measurements and screen.json → <device>/primitives.tsv, validated before writing."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import GroupingTree, RunTree
from cryptobench.paths import MEASUREMENTS, PRIMITIVES
from .. import run_dir as rd
from cryptobench.catalogue.grouping import read_items
from ..dto.primitives import SCHEMA_LINE, PrimitivesTable
from ..files import read_json, sha256_file, write_text
from ..log import step
from ..result.primitives import NotScreened, build_table, statuses
from ..validation import require, validate_measurements, validate_primitives
from ..stop.halt import Coded


def inputs(device: Path) -> dict[str, str | None]:
    """The digests the table is made from; items.json is bound into screen.json's own `built`."""
    grouping = GroupingTree(device)
    return {"rows": sha256_file(RunTree(device).rows), "measurements": sha256_file(RunTree(device).measurements),
            "screen": sha256_file(grouping.screen)}


def unusable(device: Path) -> str | None:
    """Why primitives.tsv is rebuilt whatever its inputs: absent, or written in another schema."""
    path = RunTree(device).primitives
    if not path.is_file():
        return f"{PRIMITIVES} missing"
    with open(path) as f:
        first = f.readline().rstrip("\n")
    return None if first == SCHEMA_LINE else f"{PRIMITIVES} starts {first!r}, not {SCHEMA_LINE!r}"


def status_of(device: Path) -> dict[str, str]:
    grouping = GroupingTree(device)
    screen = rd.load_screen(grouping)
    if screen is None:
        raise Coded(f"no_screen: {grouping.screen} absent; the primitives table takes each status from it")
    return statuses(read_items(read_json(grouping.items)), screen)


def write_primitives(device: Path) -> str:
    """The line to print."""
    device = Path(device)
    with step("primitives", "primitives") as s:
        rows, measurements = rd.load_rows(device), rd.load_measurements(device)
        require(MEASUREMENTS, validate_measurements(measurements, rows))
        statuses_by_name = status_of(device)
        try:
            table = build_table(rows, measurements.byRow, statuses_by_name)
        except NotScreened as e:
            raise NotScreened(e.names, RunTree(device).log.primitives_missing) from None
        text = table.to_tsv()
        # checked as it reads back, so the text form is what the validator vouches for
        require(PRIMITIVES, validate_primitives(PrimitivesTable.from_tsv(text), rows, measurements, statuses_by_name))
        write_text(RunTree(device).primitives, text)
        s.count(rows=len(rows), lines=len(table.lines), columns=len(table.header))
        s.wrote(RunTree(device).primitives)
    return f"{RunTree(device).primitives}: {len(table.lines)} lines from {len(rows)} rows, {len(text.encode())} bytes"
