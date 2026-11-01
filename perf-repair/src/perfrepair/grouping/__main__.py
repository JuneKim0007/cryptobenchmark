"""python3 -m perfrepair.grouping {build,assign,report} — the grouping stage, one step per command.
  build   --manifest <results>/manifest.yaml --run <dir>     items.json, profiles.json
  assign  --run <dir> [--agent ...] [--prompts DIR] [--turns 3] [--sessions 2] [--limit N]
  report  --run <dir> [--supervisor [--prompts DIR]] [--agent ...]   checks.json, groups.json [, supervisor.json]
  interop-plan --run <dir>                                    interop_plan.yaml from groups.json
  interop-read --run <dir> --results <interop.yaml>           interop.yaml imported; report rerun with its findings"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ai.runtime.agent.select import add_agent_args, conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from .build.stage import build_stage
from .interop_plan import write_plan
from .interop_read import import_results
from ..ai.parse.grouping_assign import command as assign_cmd
from .paths import GroupingPaths
from .report.checks import report
from ..ai.review.grouping_review import command as review_cmd


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
    add_prompt_args(a)
    a.add_argument("--turns", type=int, default=Limits.turns)
    a.add_argument("--sessions", type=int, default=Limits.sessions)
    a.add_argument("--limit", type=int, help="decide at most this many items in this call; the next call resumes")
    r = sub.add_parser("report")
    r.add_argument("--run", type=Path, required=True)
    r.add_argument("--supervisor", action="store_true", help="also review each family with a supervisor agent (findings only)")
    add_agent_args(r, effort="high")
    add_prompt_args(r)
    sub.add_parser("interop-plan").add_argument("--run", type=Path, required=True)
    ir = sub.add_parser("interop-read")
    ir.add_argument("--run", type=Path, required=True)
    ir.add_argument("--results", type=Path, required=True, help="cryptobenchmark's <results>/interop/interop.yaml")
    args = ap.parse_args(argv)

    paths = GroupingPaths(args.run)
    if args.step == "build":
        build_stage(args.manifest, args.run)
        print(f"wrote {paths.items} and {paths.profiles}")
        return 0
    if args.step == "interop-plan":
        print(f"{len(write_plan(paths))} pairs -> {paths.interop_plan}")
        return 0
    if args.step == "interop-read":
        results = import_results(paths, args.results)
        counts = {r: sum(1 for p in results if p.result == r) for r in sorted({p.result for p in results})}
        document = report(paths)
        print(f"{len(results)} pairs {counts} -> {paths.interop}; {len(document['groups'])} groups -> {paths.groups}")
        return 0
    if args.step == "report" and args.prompts is not None and not args.supervisor:
        r.error("--prompts only applies with --supervisor; report alone calls no model")
    library = load_prompts(ap, args)
    if args.step == "assign":
        assign_cmd.assign(paths, conversations(args, assign_cmd.DRY_RUN), library, Limits(args.turns, args.sessions), args.limit)
    else:
        document = report(paths)
        print(f"{len(document['groups'])} groups, {len(document['dropped'])} dropped -> {paths.groups}")
        if args.supervisor:
            review_cmd.review(paths, conversations(args, review_cmd.DRY_RUN), library)
    return 0


if __name__ == "__main__":
    sys.exit(main())
