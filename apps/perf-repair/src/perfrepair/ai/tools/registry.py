"""The tools of a run by job: a job is sent and may call only its own; a tool outside it reads as one that does not exist."""
from __future__ import annotations

import json

from ...validation.schema_walk import walk
from .tool import SUBMIT, Context, Outcome, Tool

# what the model sends on every turn: one call of one of its job's tools
CALL_FIELDS = ("tool", "args")


class Registry:

    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self.jobs: dict[str, tuple[str, ...]] = {}

    def add(self, job: str, tools: list[Tool]) -> None:
        if job in self.jobs:
            raise ValueError(f"job {job} is already registered")
        for t in tools:
            if self.tools.setdefault(t.name, t) is not t:
                raise ValueError(f"tool {t.name}: another tool of that name is registered")
        if sum(t.kind == SUBMIT for t in tools) != 1:
            raise ValueError(f"{job}: exactly one submit tool")
        _union(tools)
        self.jobs[job] = tuple(t.name for t in tools)

    def surface(self, job: str) -> list[dict]:
        """The only definitions the job's model is sent."""
        return [self.tools[n].definition() for n in self.jobs[job]]

    def reply_schema(self, job: str) -> dict:
        """One turn's answer: a tool of the job and its arguments; each tool's own schema is walked at the call."""
        tools = [self.tools[n] for n in self.jobs[job]]
        args = {"type": "object", "properties": _union(tools), "additionalProperties": False}
        return {"type": "object", "properties": {"tool": {"type": "string", "enum": [t.name for t in tools]}, "args": args},
                "required": list(CALL_FIELDS), "additionalProperties": False}

    def call(self, ctx: Context, name: str, args) -> tuple[Tool | None, Outcome]:
        tool = self.tools.get(name) if name in self.jobs.get(ctx.job, ()) else None
        if tool is None:
            out = Outcome(False, f"unknown tool {name!r}; tools: {', '.join(self.jobs.get(ctx.job, ()))}")
        elif problems := walk(args, tool.schema):
            out = Outcome(False, "; ".join(problems))
        else:
            out = tool.run(args, ctx)
            if out.ok and tool.kind == SUBMIT:
                ctx.submitted = out.value
        ctx.calls.append({"tool": name, "kind": tool.kind if tool else None, "args": json.dumps(args, sort_keys=True)[:500],
                          "ok": out.ok, **({} if out.ok else {"problem": out.text[:500]})})
        return tool, out


def _union(tools: list[Tool]) -> dict:
    """Every argument of the job's tools; one name means one schema across them."""
    out: dict = {}
    for t in tools:
        for name, schema in t.schema.get("properties", {}).items():
            if out.setdefault(name, schema) != schema:
                raise ValueError(f"argument {name} has two schemas across the job's tools")
    return out
