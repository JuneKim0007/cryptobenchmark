"""Whether an option is worse beyond noise on every selected metric it has a number for: code rejects it, the model never weighs it."""
from __future__ import annotations

from ..dto.site import Estimate
from .modes import CRITERIA
from ..files import read_yaml

CRITERIA_DOC = read_yaml(CRITERIA)
WORSE_RATIO = 1 / float(CRITERIA_DOC["improvingRatio"])
# the top level's floor, read from the other side: the option is better with at most this probability
NOISE = 1 - max(float(lv["atLeast"]) for lv in CRITERIA_DOC["levels"])


def _worse(e: Estimate) -> bool:
    return e.pImprove is not None and e.ratio >= WORSE_RATIO and e.pImprove <= NOISE


def no_gain(estimates: tuple[Estimate, ...]) -> bool:
    """Every estimate of every metric worse; none at all, or one without runs enough to say, is not evidence of no gain."""
    return bool(estimates) and all(_worse(e) for e in estimates)
