"""python3 -m perfrepair.grouping {build,assign,report} — the grouping stage, one step per command.
  build   --manifest <results>/manifest.yaml --run <dir>   items.json, profiles.json, screen.json;
          with screening.aiReview [--agent ...] [--prompts DIR] the classify model reviews the unknown items first
  assign  --run <dir> [--agent ...] [--prompts DIR] [--turns 3] [--sessions 2] [--limit N]
  report  --run <dir> [--supervisor [--prompts DIR]] [--agent ...]   checks.json, groups.json [, supervisor.json]
  interop-plan --run <dir>                                    interop_plan.yaml from groups.json
  interop-read --run <dir> --results <interop.yaml>           interop.yaml imported; report rerun with its findings
Every step fills unset values from perfrepair.yaml (--perfrepair-config FILE), --run from paths.run; see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.gateway.args import add_agent_args
from ..ai.runtime.gateway.spawn import spawn
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..config.args import add_config_arg, fill, fill_run, load_settings, positive_int
from ..inputs.table import (GROUPING_ASSIGN, GROUPING_LIMIT, GROUPING_SESSIONS, GROUPING_SUPERVISOR, GROUPING_TURNS,
                            SCREENING_CLASSIFY)
from ..config.load import Loaded
from ..failure import reported
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


RUN_HELP = "default: paths.run in perfrepair.yaml"
BUILD_MODEL_FLAGS = ("agent", "auth", "model", "effort", "prompts")


def _parser() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    ap = argparse.ArgumentParser(prog="perfrepair.grouping", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    b = sub.add_parser("build")
    b.add_argument("--manifest", type=Path, required=True)
    b.add_argument("--run", type=Path, help=RUN_HELP)
    add_agent_args(b, role=SCREENING_CLASSIFY)
    add_prompt_args(b)
    a = sub.add_parser("assign")
    a.add_argument("--run", type=Path, help=RUN_HELP)
    add_agent_args(a, role=GROUPING_ASSIGN)
    add_prompt_args(a)
    a.add_argument("--turns", type=positive_int, help=f"default: device.grouping.turns, else {Limits.turns}")
    a.add_argument("--sessions", type=positive_int, help=f"default: device.grouping.sessions, else {Limits.sessions}")
    a.add_argument("--limit", type=positive_int, help="decide at most this many items in this call; the next call resumes; "
                                             "default: device.grouping.limit, else all")
    r = sub.add_parser("report")
    r.add_argument("--run", type=Path, help=RUN_HELP)
    r.add_argument("--supervisor", action="store_true", help="also review each family with a supervisor agent (findings only)")
    add_agent_args(r, role=GROUPING_SUPERVISOR)
    add_prompt_args(r)
    ip = sub.add_parser("interop-plan")
    ip.add_argument("--run", type=Path, help=RUN_HELP)
    add_config_arg(ip)
    ir = sub.add_parser("interop-read")
    ir.add_argument("--run", type=Path, help=RUN_HELP)
    add_config_arg(ir)
    ir.add_argument("--results", type=Path, required=True, help="cryptobenchmark's <results>/interop/interop.yaml")
    return ap, sub.choices


def _model_step(ap: argparse.ArgumentParser, step: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.step == "report" and args.prompts is not None and not args.supervisor:
        step.error("--prompts only applies with --supervisor; report alone calls no model")
    settings = _with_run(ap, args)
    library = load_prompts(ap, args, settings) if args.step == "assign" or args.supervisor else None
    paths = GroupingPaths(args.run)
    if args.step == "assign":
        fill(settings, args, {"turns": GROUPING_TURNS, "sessions": GROUPING_SESSIONS, "limit": GROUPING_LIMIT})
        assign_cmd.assign(paths, spawn(args, settings, assign_cmd.DRY_RUN), library,
                          Limits(args.turns, args.sessions), args.limit)
        return
    # the spawn's errors come before the report's work
    supervisor = spawn(args, settings, review_cmd.DRY_RUN) if args.supervisor else None
    document = report(paths)
    print(f"{len(document['groups'])} groups, {len(document['dropped'])} dropped -> {paths.groups}")
    if supervisor:
        review_cmd.review(paths, supervisor, library)


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap, steps = _parser()
    args = ap.parse_args(argv)
    if args.step == "build":
        return reported(lambda: _build(ap, steps["build"], args))
    if args.step in ("assign", "report"):
        return reported(lambda: _model_step(ap, steps[args.step], args))
    return reported(lambda: _file_step(ap, args))


def _with_run(ap: argparse.ArgumentParser, args: argparse.Namespace) -> Loaded:
    settings = load_settings(ap, args)
    fill_run(ap, settings, args)
    return settings


def _build(ap: argparse.ArgumentParser, step: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    settings = _with_run(ap, args)
    reviewer = None
    if ai_review(settings):
        reviewer = Reviewer(spawn(args, settings, classify_cmd.DRY_RUN), load_prompts(ap, args, settings))
    elif given := [f"--{name}" for name in BUILD_MODEL_FLAGS if getattr(args, name) is not None]:
        step.error(f"{', '.join(given)} only apply with device.screening.aiReview; build alone calls no model")
    paths = build_stage(args.manifest, args.run, screening_catalog(settings), reviewer)
    print(f"wrote {paths.items}, {paths.profiles} and {paths.screen}")


def _file_step(ap: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    _with_run(ap, args)
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
