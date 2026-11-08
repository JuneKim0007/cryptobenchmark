"""next_tier: the next model up the gateway's ladder at the same effort; at most MAX_ESCALATIONS steps, then a person's."""
from __future__ import annotations

from dataclasses import replace

from ..model.tier import Ladder, Tier

MAX_ESCALATIONS = 1


def next_tier(tier: Tier, ladder: Ladder) -> Tier | None:
    """None past the strongest model or off the ladder; efforts are never climbed."""
    models = ladder.models
    if tier.model in models and models.index(tier.model) + 1 < len(models):
        return replace(tier, model=models[models.index(tier.model) + 1])
    return None
