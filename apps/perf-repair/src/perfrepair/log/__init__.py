"""The run log: events.jsonl and its views under <device>/log/; library code emits (cryptobench.shared.log.emit), only a command attaches."""
from .attach import attach, bug_log, command_run, run_id

__all__ = ["attach", "bug_log", "command_run", "run_id"]
