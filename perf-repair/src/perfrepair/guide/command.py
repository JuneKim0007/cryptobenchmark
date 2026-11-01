"""python3 -m perfrepair guide — one app from source to its harness (dry), or to a measured report (--device).
Needs `pip install -e perf-repair` or PYTHONPATH=perf-repair/src; `python3 scripts/llm_guide.py` sets the path."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..ai.runtime.agent.select import add_agent_args, conversations
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..ai.suggest.site_replace import command as replace_cmd
from ..app.gate import GateError
from ..data_handler.outbound.benchmark_runner import BenchmarkRunError
from ..result.modes import MODES
from ..validation import ValidationFailed
from .steps import DEVICE, DRY, Guide, Stop

FAILURES = (ValidationFailed, ValueError, OSError, GateError, BenchmarkRunError)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="perfrepair guide", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", type=Path, required=True, help="the app's source root; only read")
    ap.add_argument("--name", required=True, help="the app's folder under <run>/apps/")
    ap.add_argument("--run", type=Path, required=True,
                    help="run directory with rows.json, measurements.json and grouping/groups.json, "
                         "e.g. ~/capstone/runs/<date>-<name>")
    ap.add_argument("--results", type=Path, required=True, help="the cryptobenchmark results directory of the run")
    ap.add_argument("--mode", choices=sorted(MODES), default="latency")
    ap.add_argument("--device", action="store_true",
                    help="also measure the harness on the attached phone (cryptobenchmark pipeline.py), then report")
    ap.add_argument("--config", type=Path, help="global.yaml for the device step; default: pipeline.py's own lookup")
    ap.add_argument("--limit", type=int, help="ask the model about at most this many scopes")
    add_agent_args(ap)
    add_prompt_args(ap)
    return ap


def run_steps(g: Guide, device: bool) -> int:
    for name, step in DRY + (DEVICE if device else ()):
        try:
            detail = step(g)
        except Stop as e:
            g.echo(f"guide {name}: stop {e.code}: {e.detail}")
            return 1
        except FAILURES as e:
            g.echo(f"guide {name}: stop {name}_failed: {e}")
            return 1
        g.echo(f"guide {name}: ok: {detail}")
    if not device:
        g.echo(f"guide: dry run ends at the harness; measure with --device, or run "
               f"`python3 scripts/pipeline.py --device --harness {g.paths.harness} --results {g.paths.measured}`")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = parser()
    a = ap.parse_args(argv)
    g = Guide(a.run.expanduser(), a.app.expanduser(), a.name, a.results.expanduser(), MODES[a.mode],
              conversations(a, replace_cmd.DRY_RUN), load_prompts(ap, a), limit=a.limit, config=a.config)
    return run_steps(g, a.device)


if __name__ == "__main__":
    sys.exit(main())
