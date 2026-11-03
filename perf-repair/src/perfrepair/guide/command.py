"""python3 -m perfrepair guide — apps from source to their harness (dry), or to a measured report (--device): --app runs one,
else every apps.targets entry; the device-level steps once, then each app; exit 0 only if every app reached its last step.
Needs `pip install -e perf-repair` or PYTHONPATH=perf-repair/src; `python3 scripts/llm_guide.py` sets the path.
Unset flags come from perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ai.runtime.gateway.args import add_agent_args
from ..ai.runtime.gateway.spawn import spawn
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..ai.suggest.site_replace import command as replace_cmd
from ..config.args import fill, load_settings, perf_mode, positive_int
from ..config.device_results import add_device_results_arg, device_root
from ..config.load import Loaded
from ..dto.bundled import BundledPolicy
from ..dto.perf_mode import PerfMode
from ..inputs.check import target_path
from ..dto.change import CHANGES
from ..inputs.table import (APPS_AGENT, APPS_LIMIT, APPS_MAX_CHANGE, APPS_MEASURE, APPS_PERF_MODE, APPS_TARGETS,
                            APPS_BENCHMARK_CONFIG, BENCHMARK_CONFIG, BUNDLED_FROM_APPS, BUNDLED_ON_MISSING,
                            FILTER_BY_APPS)
from ..failure import reported
from ..log import attach
from ..result.modes import mode_of
from .steps import Guide
from .targets import run_targets


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="perfrepair guide", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", type=Path, help="run this one app, its source root; only read; its path gives the app's id; "
                                             "default: every apps.targets entry")
    add_device_results_arg(ap)
    ap.add_argument("--perf-mode", type=perf_mode, metavar="KEYS",
                    help="the metrics the model is given: generic (all), or a comma list of latency, throughput, memAlloc, "
                         "energy; default: apps.perfMode, else generic")
    ap.add_argument("--device", action="store_true", default=None,
                    help="also measure the harness on the attached phone (cryptobenchmark pipeline.py), then report; "
                         "default: apps.measure")
    ap.add_argument("--config", type=Path, help="global.yaml for the device step; default: device.benchmark.config, "
                                                "else pipeline.py's own lookup")
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
    fill(settings, a, {"device": APPS_MEASURE, "config": BENCHMARK_CONFIG, "limit": APPS_LIMIT, "perf_mode": APPS_PERF_MODE,
                         "max_change": APPS_MAX_CHANGE})
    return reported(lambda: _run(ap, a, settings))


def _grouping_args(a: argparse.Namespace) -> tuple[str, ...]:
    # a gateway named on the guide reaches every model step it runs; other keys resolve per role from the settings
    return (*(("--agent", a.agent) if a.agent else ()),
            *(("--perfrepair-config", str(a.perfrepair_config)) if a.perfrepair_config else ()))


def _roots(ap: argparse.ArgumentParser, a: argparse.Namespace, settings: Loaded) -> list[Path]:
    if a.app is not None:
        return [a.app.expanduser().resolve()]
    listed = settings.read(APPS_TARGETS)
    if not listed:
        ap.error(f"the following arguments are required: --app (or {APPS_TARGETS.key} in perfrepair.yaml)")
    # relative to the settings file, as its paths are; one app named twice runs once
    return list(dict.fromkeys((settings.file.parent / Path(target_path(e)).expanduser()).resolve() for e in listed))


def _run(ap: argparse.ArgumentParser, a: argparse.Namespace, settings: Loaded) -> int:
    roots = _roots(ap, a, settings)
    root = device_root(ap, a, settings)
    base = Guide(a.device_results, None, mode_of(PerfMode.parse(a.perf_mode)), spawn(a, settings, replace_cmd.DRY_RUN),
                 load_prompts(ap, a, settings), limit=a.limit, config=a.config, settings=settings, root=root,
                 on_device=bool(a.device), grouping_args=_grouping_args(a), refresh=a.refresh, targets=tuple(roots),
                 filter_by_apps=settings.read(FILTER_BY_APPS), app_config=settings.read(APPS_BENCHMARK_CONFIG),
                 bundled=BundledPolicy.read(settings.read(BUNDLED_ON_MISSING), settings.read(BUNDLED_FROM_APPS)),
                 max_change=a.max_change)
    return run_targets(base, roots, a.device, reuse=a.app is None)


if __name__ == "__main__":
    sys.exit(main())
