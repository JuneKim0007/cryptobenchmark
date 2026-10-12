"""python3 -m perfrepair.grouping {build,assign} — the grouping stage, one step per command.

  build   --manifest <results>/manifest.yaml --run <dir>     items.json, profiles.json
  assign  --run <dir> [--agent claude|dry-run] [--turns 3] [--sessions 2] [--model M] [--effort E]
  report  --run <dir> [--supervisor] [--agent ...]           checks.json, groups.json [, supervisor.json]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ..orchestrate.agent import ClaudeConversations, ScriptedConversations
from .build.stage import build_stage
from .loop.run import Limits, run
from .paths import GroupingPaths
from .report.checks import report
from .supervise.run import supervise


def _dry_run(message: str, *_):
    """Every item founds its own group: exercises gates, outbox and projections without a model."""
    item = re.search(r"ITEM\n  id (\d+)", message)
    if item is None:
        return {"group": "", "newGroup": {"id": "", "description": ""}, "amend": [], "reason": ""}
    return {"group": "", "newGroup": {"id": f"dry-{item.group(1)}", "description": "dry run: no model was called"},
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
    a.add_argument("--agent", choices=["claude", "dry-run"], default="claude")
    a.add_argument("--turns", type=int, default=Limits.turns)
    a.add_argument("--sessions", type=int, default=Limits.sessions)
    a.add_argument("--model", default="claude-opus-5-5")
    a.add_argument("--effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    r = sub.add_parser("report")
    r.add_argument("--run", type=Path, required=True)
    r.add_argument("--supervisor", action="store_true", help="also review each family with a supervisor agent (findings only)")
    r.add_argument("--agent", choices=["claude", "dry-run"], default="claude")
    r.add_argument("--model", default="claude-opus-5-5")
    r.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    args = ap.parse_args(argv)

    if args.step == "report":
        paths = GroupingPaths(args.run)
        document = report(paths)
        print(f"{len(document['groups'])} groups, {len(document['dropped'])} dropped -> {paths.groups}")
        if args.supervisor:
            reviewer = (ScriptedConversations(lambda *_: {"findings": []}) if args.agent == "dry-run"
                        else ClaudeConversations(args.model, args.effort))
            supervise(paths, reviewer)
        return 0

    if args.step == "build":
        paths = build_stage(args.manifest, args.run)
        print(f"wrote {paths.items} and {paths.profiles}")
        return 0
    conversations = ScriptedConversations(_dry_run) if args.agent == "dry-run" else ClaudeConversations(args.model, args.effort)
    knowledge = run(GroupingPaths(args.run), conversations, limits=Limits(args.turns, args.sessions))
    print(f"{len(knowledge.groups)} groups, {len(knowledge.dropped)} dropped, knowledge version {knowledge.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
