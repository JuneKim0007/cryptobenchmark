"""The reader of <device>/primitives.tsv."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import RunTree
from ...dto.primitives import PrimitivesTable
from ...files import read_text


def read_primitives(device: Path) -> PrimitivesTable:
    return PrimitivesTable.from_tsv(read_text(RunTree(device).primitives))
