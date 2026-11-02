"""python3 -m perfrepair guide — one app from source to its harness (dry), or to a measured report (--device).
Needs `pip install -e perf-repair` or PYTHONPATH=perf-repair/src; `python3 scripts/llm_guide.py` sets the path.
Unset flags come from perfrepair.yaml (--perfrepair-config FILE); see docs/settings.md."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ..ai.runtime.gateway.args import add_agent_args
from ..ai.runtime.gateway.spawn import spawn
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..ai.suggest.site_replace import command as replace_cmd
from ..config.args import fill, load_settings, positive_int
from ..config.device_results import add_device_results_arg, device_root
from ..config.load import Loaded
from ..inputs.check import check_one_of
from ..inputs.table import APPS_AGENT, APPS_LIMIT, APPS_MEASURE, APPS_MODE, BENCHMARK_CONFIG
from ..failure import FAILURES, reported
from ..dto.event import END
from ..log import attach, emit
from ..log.emit import elapsed_ms
from ..result.modes import MODES
from .steps import DEVICE, DRY, Guide, Stop


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="perfrepair guide", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", type=Path, required=True, help="the app's source root; only read; its path gives the app's id")
    add_device_results_arg(ap)
    ap.add_argument("--mode", choices=sorted(MODES), help="default: apps.mode, else latency")
    ap.add_argument("--device", action="store_true", default=None,
                    help="also measure the harness on the attached phone (cryptobenchmark pipeline.py), then report; "
                         "default: apps.measure")
    ap.add_argument("--config", type=Path, help="global.yaml for the device step; default: device.benchmark.config, "
                                                "else pipeline.py's own lookup")
    ap.add_argument("--limit", type=positive_int, help="ask the model about at most this many scopes; default: apps.limit")
    add_agent_args(ap, role=APPS_AGENT)
    add_prompt_args(ap)
    return ap


def _step(g: Guide, name: str, step) -> bool:
    started = time.monotonic()
    try:
        detail = step(g)
    except Stop as e:
        outcome, line = "stop", f"stop {e.code}: {e.detail}"
    except FAILURES as e:
        outcome, line = "stop", f"stop {name}_failed: {e}"
    else:
        outcome, line = "ok", f"ok: {detail}"
    # prerequisites names the device folder when probe_device made it
    if g.device is not None:
        attach(g.device)
    emit("guide", name, END, app=g.app_id, outcome=outcome, durationMs=elapsed_ms(started), detail=line)
    g.echo(f"guide {name}: {line}")
    return outcome == "ok"


def run_steps(g: Guide, device: bool) -> int:
    for name, step in DRY + (DEVICE if device else ()):
        if not _step(g, name, step):
            return 1
    if not device:
        g.echo(f"guide: dry run ends at the harness; measure with --device, or run "
               f"`python3 scripts/pipeline.py --device --harness {g.paths.harness}`")
    return 0


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = parser()
    a = ap.parse_args(argv)
    settings = load_settings(ap, a)
    fill(settings, a, {"device": APPS_MEASURE, "config": BENCHMARK_CONFIG, "limit": APPS_LIMIT})
    # modes come from result/criteria.yaml, a layer above the rows
    a.mode = settings.read(APPS_MODE, a.mode, lambda name, value: check_one_of(name, value, tuple(sorted(MODES))))
    return reported(lambda: _run(ap, a, settings))


def _grouping_args(a: argparse.Namespace) -> tuple[str, ...]:
    # a gateway named on the guide reaches every model step it runs; other keys resolve per role from the settings
    return (*(("--agent", a.agent) if a.agent else ()),
            *(("--perfrepair-config", str(a.perfrepair_config)) if a.perfrepair_config else ()))


def _run(ap: argparse.ArgumentParser, a: argparse.Namespace, settings: Loaded) -> int:
    root = device_root(ap, a, settings)
    return run_steps(Guide(a.device_results, a.app.expanduser().resolve(), MODES[a.mode], spawn(a, settings, replace_cmd.DRY_RUN),
                           load_prompts(ap, a, settings), limit=a.limit, config=a.config, settings=settings, root=root,
                           on_device=bool(a.device), grouping_args=_grouping_args(a)), a.device)


if __name__ == "__main__":
    sys.exit(main())
