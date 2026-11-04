"""The one writer of log/details/benchmark_coverage.yaml: the gate's last check, rewritten whole and atomically at each
gate point, with the attempt and the delta it ran; no stage reads it back."""
from __future__ import annotations

from pathlib import Path

import yaml

from .. import run_dir as rd
from ..dto.benchmark_coverage import Coverage, coverage_document
from ..files import write_text_making_parents
from ..log import run_id
from ..validation import require
from ..validation.benchmark_coverage import validate_coverage


def write_coverage(device: Path, point: str, attempt: int, coverage: Coverage, delta: dict | None = None) -> Path:
    doc = coverage_document(run_id(), point, attempt, coverage, delta)
    require(rd.BENCHMARK_COVERAGE, validate_coverage(doc))
    return write_text_making_parents(Path(device) / rd.BENCHMARK_COVERAGE, yaml.safe_dump(doc, sort_keys=False))
