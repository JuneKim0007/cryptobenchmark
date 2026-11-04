"""The one rule of a metric's change: per estimate improved, worse or unchanged, beyond noise and improvingRatio; an
option's label over its metrics; and whether an option is proven worse with nothing better, which code rejects."""
from __future__ import annotations

from ..dto.dossier import Estimate
from .modes import criteria, worse_ratio

IMPROVING_RATIO = float(criteria()["improvingRatio"])
WORSE_RATIO = worse_ratio(IMPROVING_RATIO)
# the top level's floor, read from the other side: the option is better with at most this probability
NOISE = 1 - max(float(lv["atLeast"]) for lv in criteria()["levels"])

IMPROVED, WORSE, UNCHANGED = "improved", "worse", "unchanged"
BEYOND, WITHIN, UNKNOWN = "beyond", "within", "unknown"
L_IMPROVES, L_TRADE_OFF, L_WORSE, L_UNCHANGED, L_NOT_MEASURED = "improves", "trade_off", "worse", "unchanged", "not_measured"
LABELS = (L_IMPROVES, L_TRADE_OFF, L_WORSE, L_UNCHANGED, L_NOT_MEASURED)


def noise_of(pImprove: float | None) -> str:
    """Whether the bootstrap tells the sides apart; two runs or fewer on a side cannot say."""
    if pImprove is None:
        return UNKNOWN
    return BEYOND if pImprove >= 1 - NOISE or pImprove <= NOISE else WITHIN


def change_of(ratio: float | None, pImprove: float | None) -> str:
    if ratio is None or noise_of(pImprove) != BEYOND:
        return UNCHANGED
    if ratio <= IMPROVING_RATIO and pImprove >= 1 - NOISE:
        return IMPROVED
    return WORSE if ratio >= WORSE_RATIO and pImprove <= NOISE else UNCHANGED


def label_of(changes: list[str]) -> str:
    """An option's overall label from its metrics' changes; no change at all is not measured."""
    if not changes:
        return L_NOT_MEASURED
    better, worse = IMPROVED in changes, WORSE in changes
    if better and worse:
        return L_TRADE_OFF
    return L_IMPROVES if better else L_WORSE if worse else L_UNCHANGED


def by_change(estimates: tuple[Estimate, ...], change: str) -> list[str]:
    """The metrics with an estimate of this change, in estimate order, each once."""
    return list(dict.fromkeys(e.metric for e in estimates if change_of(e.ratio, e.pImprove) == change))


def option_label(estimates: tuple[Estimate, ...]) -> str:
    return label_of([change_of(e.ratio, e.pImprove) for e in estimates])


def strict_passes(estimates: tuple[Estimate, ...]) -> bool:
    """A listed perfMode's rule, the verdict's: a metric at or below improvingRatio and none at or above its inverse;
    pImprove grades, it never rejects."""
    return any(e.ratio <= IMPROVING_RATIO for e in estimates) and not any(e.ratio >= WORSE_RATIO for e in estimates)


def _worse(e: Estimate) -> bool:
    return e.pImprove is not None and e.ratio >= WORSE_RATIO and e.pImprove <= NOISE


def no_gain(estimates: tuple[Estimate, ...]) -> bool:
    """One metric proven worse and none better; a single-window energy reading can neither prove nor save."""
    return any(_worse(e) for e in estimates) and not any(e.ratio <= IMPROVING_RATIO for e in estimates)
