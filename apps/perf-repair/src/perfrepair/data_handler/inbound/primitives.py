"""The reader of <device>/primitives.tsv."""
from __future__ import annotations

from pathlib import Path

from ... import run_dir as rd
from ...dto.primitives import PrimitivesTable
from ...files import read_text


def read_primitives(device: Path) -> PrimitivesTable:
    return PrimitivesTable.from_tsv(read_text(Path(device) / rd.PRIMITIVES))
