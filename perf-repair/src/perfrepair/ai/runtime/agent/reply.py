from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class AgentReply:
    text: str
    model: str = ""
    requestId: str = ""
    usage: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return asdict(self)


class AgentRefused(RuntimeError):
    """The model declined the request (stop_reason "refusal")."""
