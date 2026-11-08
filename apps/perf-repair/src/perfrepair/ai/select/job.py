"""Select: the model submits one of code's candidates for the item, or none where none is allowed, with a reason; code
writes every edit, risk and metric from the candidate."""
from __future__ import annotations

from pathlib import Path

from ...files import write_json
from ...validation import require
from ..job import Job
from ..tools.tool import args_schema
from .candidate import NONE, SelectItem

NAME = "select"


class SelectJob(Job):
    name = NAME
    prompt = NAME
    submit_description = "your choice: one candidate's alias, or none where the message allows it, and why"
    submit_schema = args_schema({"option": {"type": "string", "pattern": r"\S"}, "reason": {"type": "string", "pattern": r"\S"}},
                                ("option", "reason"))

    def __init__(self, spawned, library, log, registry, source, limits=None, reviewer: Job | None = None):
        self.source = source
        extra = {"limits": limits} if limits is not None else {}
        super().__init__(spawned, library, log, registry, store=Path(source.folder), reviewer=reviewer, **extra)

    def candidates(self) -> list[SelectItem]:
        return self.source.items()

    def label(self, item: SelectItem) -> str:
        return item.label

    def evidence(self, item: SelectItem) -> str:
        return item.evidence

    def render(self, item: SelectItem) -> str:
        return item.text

    def checks(self, item: SelectItem, args: dict) -> list[str]:
        if args["option"] in item.answers():
            return []
        return [f"option {args['option']!r} is not one of {', '.join(item.answers())}"]

    def reviews(self, item: SelectItem, args: dict) -> bool:
        """Only a pick that will edit code is reviewed: none, a keep or a person's needs are not."""
        return args["option"] != NONE and self.source.edits_code(item, item.by_alias()[args["option"]])

    def decide(self, item: SelectItem, args: dict) -> dict:
        chosen = None if args["option"] == NONE else item.by_alias()[args["option"]]
        return self.source.decide(item, chosen, args["reason"].strip())

    def unidentified(self, item: SelectItem, reason: str) -> dict:
        return self.source.unidentified(item, reason)

    def apply(self, item: SelectItem, record) -> None:
        self.source.apply(item, record)

    def finish(self) -> None:
        require(self.name, self.source.state_problems())
        for path, document in self.source.documents().items():
            write_json(path, document)
