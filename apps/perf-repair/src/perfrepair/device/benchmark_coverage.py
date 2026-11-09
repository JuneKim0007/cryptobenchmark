"""CoverageFile: the one writer of log/details/benchmark_coverage.yaml. The gate's last check, rewritten whole and atomically,
with each point's delta count and the deltas this run merged held in memory; no stage reads the file back."""
from __future__ import annotations

from pathlib import Path

import yaml

from cryptobench.paths import RunTree
from cryptobench.paths import BENCHMARK_COVERAGE
from ..dto.benchmark_coverage import Coverage, coverage_document
from ..files import write_text_making_parents
from ..log import run_id
from ..validation import require
from ..validation.benchmark_coverage import validate_coverage


class CoverageFile:
    def __init__(self):
        self.attempts: dict[str, int] = {}
        self.deltas: list[dict] = []

    def write(self, device: Path, point: str, coverage: Coverage, delta: dict | None = None) -> Path:
        """delta: the one this point just ran."""
        self.attempts[point] = self.attempts.get(point, 0) + bool(delta)
        self.deltas += [delta] if delta else []
        doc = coverage_document(run_id(), point, self.attempts, coverage, self.deltas)
        require(BENCHMARK_COVERAGE, validate_coverage(doc))
        return write_text_making_parents(RunTree(device).log.benchmark_coverage, yaml.safe_dump(doc, sort_keys=False))


def clear_coverage(device: Path) -> None:
    """No used set, so no check ran: nothing an earlier run left may read as this run's."""
    (RunTree(device).log.benchmark_coverage).unlink(missing_ok=True)
