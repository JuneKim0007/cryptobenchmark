"""python3 -m perfrepair.grouping {build,assign,report} — the grouping stage, one step per command.
  build   --manifest <results>/manifest.yaml --run <dir> [--agent ...]   items.json, profiles.json, screen.json;
          with screening.aiReview the classify model reviews the unknown items first
  assign  --run <dir> [--agent ...] [--prompts DIR] [--turns 3] [--sessions 2] [--limit N]
  report  --run <dir> [--supervisor [--prompts DIR]] [--agent ...]   checks.json, groups.json [, supervisor.json]
  interop-plan --run <dir>                                    interop_plan.yaml from groups.json
  interop-read --run <dir> --results <interop.yaml>           interop.yaml imported; report rerun with its findings
build, assign and report fill unset values from perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ai.runtime.agent.select import add_agent_args, conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..config.args import fill, load_settings, require
from ..log import log_to_stderr
from ..screen.catalog import ai_review, screening_catalog
from .build.stage import build_stage
from .interop_plan import write_plan
from .interop_read import import_results
from ..ai.parse.algorithm_classify import command as classify_cmd
from ..ai.parse.algorithm_classify.command import Reviewer
from ..ai.parse.grouping_assign import command as assign_cmd
from ..run_dir import GroupingPaths
from .report.checks import report
from ..ai.review.grouping_review import command as review_cmd
from ..validation import ValidationFailed


def _parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    ap = argparse.ArgumentParser(prog="perfrepair.grouping", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    b = sub.add_parser("build")
    b.add_argument("--manifest", type=Path, required=True)
    b.add_argument("--run", type=Path, required=True)
    add_agent_args(b, role="screening.classify")
    add_prompt_args(b)
    a = sub.add_parser("assign")
    a.add_argument("--run", type=Path, help="default: paths.run in perfrepair.yaml")
    add_agent_args(a, role="grouping.assign")
    add_prompt_args(a)
    a.add_argument("--turns", type=int, help=f"default: grouping.turns, else {Limits.turns}")
    a.add_argument("--sessions", type=int, help=f"default: grouping.sessions, else {Limits.sessions}")
    a.add_argument("--limit", type=int, help="decide at most this many items in this call; the next call resumes; "
                                             "default: grouping.limit, else all")
    r = sub.add_parser("report")
    r.add_argument("--run", type=Path, help="default: paths.run in perfrepair.yaml")
    r.add_argument("--supervisor", action="store_true", help="also review each family with a supervisor agent (findings only)")
    add_agent_args(r, role="grouping.supervisor")
    add_prompt_args(r)
    sub.add_parser("interop-plan").add_argument("--run", type=Path, required=True)
    ir = sub.add_parser("interop-read")
    ir.add_argument("--run", type=Path, required=True)
    ir.add_argument("--results", type=Path, required=True, help="cryptobenchmark's <results>/interop/interop.yaml")
    return ap, sub.choices


def _model_step(ap: argparse.ArgumentParser, step: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.step == "report" and args.prompts is not None and not args.supervisor:
        step.error("--prompts only applies with --supervisor; report alone calls no model")
    settings = load_settings(ap, args)
    fill(settings, args, {"run": ("paths.run", None)})
    require(ap, args, "run", "paths.run")
    if args.step == "assign" or args.supervisor:
        fill(settings, args, {"prompts": ("paths.prompts", None)})
    library = load_prompts(ap, args)
    paths = GroupingPaths(args.run)
    if args.step == "assign":
        fill(settings, args, {"turns": ("grouping.turns", Limits.turns), "sessions": ("grouping.sessions", Limits.sessions),
                              "limit": ("grouping.limit", None)})
        assign_cmd.assign(paths, conversations(args, settings, assign_cmd.DRY_RUN), library,
                          Limits(args.turns, args.sessions), args.limit)
        return
    document = report(paths)
    print(f"{len(document['groups'])} groups, {len(document['dropped'])} dropped -> {paths.groups}")
    if args.supervisor:
        review_cmd.review(paths, conversations(args, settings, review_cmd.DRY_RUN), library)


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap, steps = _parser()
    args = ap.parse_args(argv)
    if args.step == "build":
        return _build(ap, args)
    if args.step in ("assign", "report"):
        _model_step(ap, steps[args.step], args)
        return 0
    try:
        _file_step(args)
    except (FileNotFoundError, ValueError, ValidationFailed) as e:
        print(f"error {e}", file=sys.stderr)
        return 1
    return 0


def _build(ap: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    settings = load_settings(ap, args)
    reviewer = None
    if ai_review(settings):
        fill(settings, args, {"prompts": ("paths.prompts", None)})
        reviewer = Reviewer(conversations(args, settings, classify_cmd.DRY_RUN), load_prompts(ap, args))
    try:
        paths = build_stage(args.manifest, args.run, screening_catalog(settings), reviewer)
    except (FileNotFoundError, ValueError, ValidationFailed) as e:
        print(f"error {e}", file=sys.stderr)
        return 1
    print(f"wrote {paths.items}, {paths.profiles} and {paths.screen}")
    return 0


def _file_step(args: argparse.Namespace) -> None:
    paths = GroupingPaths(args.run)
    if args.step == "interop-plan":
        print(f"{len(write_plan(paths))} pairs -> {paths.interop_plan}")
    else:
        results = import_results(paths, args.results)
        counts = {r: sum(1 for p in results if p.result == r) for r in sorted({p.result for p in results})}
        document = report(paths)
        print(f"{len(results)} pairs {counts} -> {paths.interop}; {len(document['groups'])} groups -> {paths.groups}")


if __name__ == "__main__":
    sys.exit(main())
