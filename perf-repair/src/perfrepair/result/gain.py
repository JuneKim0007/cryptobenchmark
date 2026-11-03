"""Whether an option is proven worse with nothing better to show for it: code rejects it, the model never weighs it."""
from __future__ import annotations

from ..dto.site import Estimate
from .modes import CRITERIA
from ..files import read_yaml

CRITERIA_DOC = read_yaml(CRITERIA)
IMPROVING_RATIO = float(CRITERIA_DOC["improvingRatio"])
WORSE_RATIO = 1 / IMPROVING_RATIO
# the top level's floor, read from the other side: the option is better with at most this probability
NOISE = 1 - max(float(lv["atLeast"]) for lv in CRITERIA_DOC["levels"])


def _worse(e: Estimate) -> bool:
    return e.pImprove is not None and e.ratio >= WORSE_RATIO and e.pImprove <= NOISE


def no_gain(estimates: tuple[Estimate, ...]) -> bool:
    """One metric proven worse and none better; a single-window energy reading can neither prove nor save."""
    return any(_worse(e) for e in estimates) and not any(e.ratio <= IMPROVING_RATIO for e in estimates)
