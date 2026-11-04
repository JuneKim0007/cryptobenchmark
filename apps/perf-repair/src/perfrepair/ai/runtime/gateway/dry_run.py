from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..agent.conversation import Conversations
from .contract import Gateway


@dataclass(frozen=True)
class DryRunSettings:
    pass


def _spawn(_values: Any, dry_run: Conversations) -> Conversations:
    return dry_run


GATEWAY = Gateway("dry-run", DryRunSettings, _spawn)
