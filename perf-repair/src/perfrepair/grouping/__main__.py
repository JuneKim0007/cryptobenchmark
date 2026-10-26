"""python3 -m perfrepair.grouping {build,assign,report} — the grouping stage, one step per command.
  build   --manifest <results>/manifest.yaml --run <dir>     items.json, profiles.json
  assign  --run <dir> [--agent ...] [--turns 3] [--sessions 2] [--limit N]
  report  --run <dir> [--supervisor] [--agent ...]          checks.json, groups.json [, supervisor.json]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..dto.prompt import TaskPrompt
from ..orchestrate.agent import ScriptedConversations
from ..orchestrate.agent.select import add_agent_args, conversations
from ..orchestrate.engine.ask import Limits
from ..orchestrate.engine.decide import decide
from ..orchestrate.prompt import PromptLibrary
from .build.stage import build_stage
from .kind import GroupingKind, charter
from .paths import GroupingPaths
from .report.checks import report
from .supervise.run import charter as supervisor_charter, supervise


def _dry_run(task: TaskPrompt, *_):
    return {"group": "", "newGroup": {"id": f"dry-{task.item}", "description": "dry run: no model was called"},
            "amend": [], "reason": "dry run"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.grouping", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    b = sub.add_parser("build")
    b.add_argument("--manifest", type=Path, required=True)
    b.add_argument("--run", type=Path, required=True)
    a = sub.add_parser("assign")
    a.add_argument("--run", type=Path, required=True)
    add_agent_args(a)
    a.add_argument("--turns", type=int, default=Limits.turns)
    a.add_argument("--sessions", type=int, default=Limits.sessions)
    a.add_argument("--limit", type=int, help="decide at most this many items in this call; the next call resumes")
    r = sub.add_parser("report")
    r.add_argument("--run", type=Path, required=True)
    r.add_argument("--supervisor", action="store_true", help="also review each family with a supervisor agent (findings only)")
    add_agent_args(r, effort="high")
    args = ap.parse_args(argv)

    paths = GroupingPaths(args.run)
    if args.step == "build":
        build_stage(args.manifest, args.run)
        print(f"wrote {paths.items} and {paths.profiles}")
    elif args.step == "assign":
        knowledge = decide(GroupingKind(paths), charter(PromptLibrary.load()), conversations(args, ScriptedConversations(_dry_run)), paths.root,
                           Limits(args.turns, args.sessions), args.limit)
        print(f"{len(knowledge.groups)} groups, {len(knowledge.dropped)} dropped, knowledge version {knowledge.version}")
    else:
        document = report(paths)
        print(f"{len(document['groups'])} groups, {len(document['dropped'])} dropped -> {paths.groups}")
        if args.supervisor:
            supervise(paths, supervisor_charter(PromptLibrary.load()), conversations(args, ScriptedConversations(lambda *_: {"findings": []})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
