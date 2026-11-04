"""A role's token budget, checked once for every role: system prompt plus task message by chars/4, before any call."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ....dto.prompt import CorrectionPrompt, SystemPrompt, TaskPrompt
from ....stop.halt import Coded

CHARS_PER_TOKEN = 4


class OverBudget(Coded):
    pass


@dataclass(frozen=True)
class Budget:
    key: str
    tokens: int


@dataclass(frozen=True)
class Fit:
    message: TaskPrompt
    narrowedFrom: int | None = None


def measure(system: SystemPrompt, message: TaskPrompt | CorrectionPrompt) -> int:
    return -(-(len(system.text) + len(message.text)) // CHARS_PER_TOKEN)


def fit(budget: Budget | None, system: SystemPrompt, message: TaskPrompt, narrow: Callable[[], TaskPrompt] | None) -> Fit:
    """The message to send; over budget, the kind's narrowed one; still over, a coded stop. Never a cut message."""
    size = measure(system, message)
    if budget is None or size <= budget.tokens:
        return Fit(message)
    narrowed = narrow() if narrow else None
    final = measure(system, narrowed) if narrowed else size
    if final > budget.tokens:
        before = f" ({size} before the exact-fact prefilter)" if narrowed else ""
        raise OverBudget(f"over_budget: {budget.key} is {budget.tokens}, item {message.item} measures {final} tokens "
                         f"by chars/4{before}")
    return Fit(narrowed, size)
