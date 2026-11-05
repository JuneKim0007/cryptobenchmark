from __future__ import annotations

from dataclasses import replace

from ..catalog.names import Names
from ..catalog.screening import Screening
from ..dto.grouping import KEY_PROVIDER_HELD, Item, Profile
from ..dto.screen import Verdict
from .handler import ScreeningHandler


def screen_items(screening: Screening, names: Names, items: list[Item], profiles: dict[int, Profile]) -> dict[int, Verdict]:
    handler = ScreeningHandler(screening, names)
    return {i.id: replace(handler.verdict(i.type, i.name, i.provider),
                          providerHeld=profiles[i.id].keyContract == KEY_PROVIDER_HELD) for i in items}
