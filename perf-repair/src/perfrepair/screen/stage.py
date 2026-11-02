from __future__ import annotations

from ..data_handler.inbound import RunContext
from ..dto.grouping import Item
from ..dto.screen import Verdict
from .handler import ScreeningHandler


def screen_items(context: RunContext, items: list[Item]) -> dict[int, Verdict]:
    handler = ScreeningHandler(context.screening, context.names)
    return {i.id: handler.verdict(i.type, i.name, i.provider) for i in items}
