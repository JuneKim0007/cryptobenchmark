"""The run log: events.jsonl and its views under <device>/log/; library code emits, only a command attaches."""
from .attach import attach, bug_log, command_run
from .emit import emit, step

__all__ = ["attach", "bug_log", "command_run", "emit", "step"]
