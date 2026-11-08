"""A run's perfMode as the mode the guide and report carry, and the improving ratio criteria.yaml holds."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto.perf_mode import PerfMode
from ..files import read_yaml

CRITERIA = Path(__file__).with_name("criteria.yaml")


@cache
def criteria() -> dict:
    return read_yaml(CRITERIA)


def worse_ratio(improving: float) -> float:
    return 1 / improving


@dataclass(frozen=True)
class Mode:
    perf: PerfMode

    @property
    def name(self) -> str:
        return self.perf.name


def mode_of(perf: PerfMode) -> Mode:
    return Mode(perf)
