"""The run log's views and readers: events.jsonl, status.log, bug.log under <device>/log/; library code emits (cryptobench.shared.log.emit), only a command attaches."""
from .attach import attach

__all__ = ["attach"]
