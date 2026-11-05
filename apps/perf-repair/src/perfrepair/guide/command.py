"""python3 -m perfrepair guide — apps from source to their harness (dry), or to a measured report (--device): --app runs one,
else every apps.targets entry; the device-level steps once, then each app; exit 0 only if every app reached its last step.
The lower-level command under `apps/cli/facade.py`, which runs the benchmark then this; needs `pip install -e apps/perf-repair`
or PYTHONPATH=apps/perf-repair/src. Unset flags come from perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..ai.runtime.gateway.args import add_agent_args
from ..ai.runtime.gateway.spawn import spawn
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..ai.repair.upgrade import command as upgrade_cmd
from ..ai.suggest.site_replace import command as replace_cmd
from ..app.facts.target_set import TargetSet, resolve_targets
from ..config.args import fill, load_settings, perf_mode, positive_int, run_id
from ..config.device_results import add_device_results_arg, device_root
from ..config.load import Loaded
from ..device.primitives_missing import MissingList
from ..dto.bundled import BundledPolicy
from ..dto.change import CHANGES
from ..dto.perf_mode import PerfMode
from ..failure import last_failure, reported
from ..files import read_json
from ..inputs.table import (
    APPS_AGENT,
    APPS_LIMIT,
    APPS_MAX_CHANGE,
    APPS_MEASURE,
    APPS_PERF_MODE,
    APPS_TARGETS,
    BUNDLED_FROM_APPS,
    FILTER_BY_APPS,
)
from ..log import attach
from ..result.modes import Mode, mode_of
from ..run_dir.run_record import ON_EXISTING, OVERWRITE
from ..stop import terminate
from .outcome import write_outcome
from .state import Guide
from .targets import run_targets

LOG = logging.getLogger(__name__)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="perfrepair guide", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", type=Path, help="run this one app, its source root; only read; its path gives the app's id; "
                                             "default: every apps.targets entry")
    add_device_results_arg(ap)
    ap.add_argument("--perf-mode", type=perf_mode, metavar="KEYS",
                    help="the metrics the model is given: generic or all (every metric, overall judgement), or a comma list of latency, throughput, memAlloc, "
                         "energy; default: apps.perfMode, else generic")
    ap.add_argument("--device", action="store_true", default=None,
                    help="also measure the harness on the attached phone (cryptobenchmark pipeline.py), then report; "
                         "default: apps.measure")
    ap.add_argument("--config", type=Path, help="global.yaml for the device stage and the device step; default: "
                                                "pipeline.py's own lookup")
    ap.add_argument("--harness-config", type=Path, metavar="FILE",
                    help="a lighter global.yaml for the per-app device step only; default: --config")
    ap.add_argument("--run-id", type=run_id, help="names runs/run_<id>.json; default: a new timestamp id")
    ap.add_argument("--on-existing", choices=ON_EXISTING, default=OVERWRITE,
                    help="a --run-id whose record exists: overwrite reruns every app and the device benchmark, resume "
                         "skips done apps, skip stops with run_exists; default: overwrite")
    ap.add_argument("--stop-after-device", action="store_true",
                    help="end after the device stage: target detect, used set, benchmark, inbound; no model is called")
    ap.add_argument("--outcome", type=Path, metavar="FILE", help="write {device, run, exit, code} here as JSON at the end")
    ap.add_argument("--run-settings", type=Path, metavar="FILE",
                    help="a JSON document stored under `settings` in the run's record: the settings tree of a facade run")
    ap.add_argument("--max-change", choices=CHANGES,
                    help="the highest change class an option may have; higher ones are reported as recommendations, "
                         "never applied; default: apps.maxChange, else drop-in")
    ap.add_argument("--limit", type=positive_int, help="ask the model about at most this many scopes; default: apps.limit")
    ap.add_argument("--refresh", action="store_true",
                    help="ask again the scopes whose dossier changed since their replace decision, and rebuild the "
                         "device's primitives.tsv; default: the app stops with dossier_changed and its report flags "
                         "them stale")
    add_agent_args(ap, role=APPS_AGENT)
    add_prompt_args(ap)
    return ap


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = parser()
    a = ap.parse_args(argv)
    settings = load_settings(ap, a)
    # a flag outranks an entry's own perfMode as it outranks apps.perfMode
    a.perf_mode_named = a.perf_mode is not None
    fill(settings, a, {"device": APPS_MEASURE, "limit": APPS_LIMIT, "perf_mode": APPS_PERF_MODE,
                         "max_change": APPS_MAX_CHANGE})
    missing, held = MissingList(), []
    try:
        code = reported(lambda: _run(ap, a, settings, missing, held))
        if a.outcome:
            write_outcome(a.outcome, held[0] if held else None, code, last_failure())
        return code
    finally:
        # last of all the guide prints: after the summary, and after a stop's own error line
        missing.announce(print)


def _grouping_args(a: argparse.Namespace) -> tuple[str, ...]:
    # a gateway named on the guide reaches every model step it runs; other keys resolve per role from the settings
    return (*(("--agent", a.agent) if a.agent else ()), *_config_args(a))


def _config_args(a: argparse.Namespace) -> tuple[str, ...]:
    return ("--perfrepair-config", str(a.perfrepair_config)) if a.perfrepair_config else ()


def _targets(ap: argparse.ArgumentParser, a: argparse.Namespace, settings: Loaded) -> TargetSet | None:
    """None with --app; else apps.targets resolved, every skip echoed; no app is a stop before any device step."""
    if a.app is not None:
        return None
    listed = settings.read(APPS_TARGETS)
    if not listed:
        ap.error(f"the following arguments are required: --app (or {APPS_TARGETS.key} in perfrepair.yaml)")
    found = resolve_targets(listed, settings.file)
    for warning in found.warnings:
        LOG.warning(f"warning: {warning}")
    for s in found.skipped:
        print(f"guide targets: skip {s.path} {s.kind}: {s.reason}")
    if not found.apps:
        terminate("no_targets", f"{len(found.skipped)} candidates skipped, none an app", stage="guide", step="targets")
    return found


def _app_modes(a: argparse.Namespace, found: TargetSet | None) -> dict[Path, Mode]:
    """Each target naming its own perfMode, by path; an app run alone or under --perf-mode takes the flag or default."""
    if found is None or a.perf_mode_named:
        return {}
    return {t.path: mode_of(t.perfMode) for t in found.apps if t.perfMode is not None}


def _run(ap: argparse.ArgumentParser, a: argparse.Namespace, settings: Loaded, missing: MissingList, held: list) -> int:
    found = _targets(ap, a, settings)
    roots = [a.app.expanduser().resolve()] if found is None else [t.path for t in found.apps]
    root = device_root(ap, a, settings)
    base = Guide(a.device_results, None, mode_of(PerfMode.parse(a.perf_mode)), spawn(a, settings, replace_cmd.DRY_RUN),
                 load_prompts(ap, a, settings), limit=a.limit, config=a.config, settings=settings, root=root,
                 on_device=bool(a.device), grouping_args=_grouping_args(a), config_args=_config_args(a), refresh=a.refresh, targets=tuple(roots),
                 filter_by_apps=settings.read(FILTER_BY_APPS), app_config=a.harness_config,
                 bundled=BundledPolicy.read(settings.read(BUNDLED_FROM_APPS)),
                 max_change=a.max_change, app_modes=_app_modes(a, found), target_set=found,
                 run_id=a.run_id, on_existing=a.on_existing, missing=missing, stop_after_device=a.stop_after_device,
                 run_settings=read_json(a.run_settings) if a.run_settings else None,
                 upgrader=spawn(argparse.Namespace(**{**vars(a), "agent_role": upgrade_cmd.ROLE}), settings, upgrade_cmd.DRY_RUN))
    held.append(base)
    return run_targets(base, roots, a.device, reuse=a.app is None)


if __name__ == "__main__":
    sys.exit(main())
