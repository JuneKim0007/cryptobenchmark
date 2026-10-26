from __future__ import annotations

from pathlib import Path

DIRECTORY = "grouping"


class GroupingPaths:

    def __init__(self, run: Path):
        self.root = Path(run) / DIRECTORY

    items = property(lambda self: self.root / "items.json")
    profiles = property(lambda self: self.root / "profiles.json")
    cursor = property(lambda self: self.root / "cursor.json")
    knowledge = property(lambda self: self.root / "knowledge.json")
    journal = property(lambda self: self.root / "journal.jsonl")
    errors = property(lambda self: self.root / "errors.jsonl")
    checks = property(lambda self: self.root / "checks.json")
    supervisor = property(lambda self: self.root / "supervisor.json")
    supervisor_journal = property(lambda self: self.root / "supervisor.journal.jsonl")
    groups = property(lambda self: self.root / "groups.json")
