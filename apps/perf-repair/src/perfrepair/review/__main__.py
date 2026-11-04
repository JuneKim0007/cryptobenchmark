"""python3 -m perfrepair.review sheet|score <device>: writes <device>/review/decisions.tsv, then prints what its verdicts score;
python3 -m perfrepair.review stability <device> --sample N --asks K [--agent ...]: asks N sampled replace units K times each."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..ai.runtime.gateway.args import add_agent_args
from ..ai.runtime.gateway.spawn import spawn
from ..ai.runtime.prompt.args import add_prompt_args, load_prompts
from ..ai.suggest.site_replace.command import DRY_RUN, ROLE
from ..config.args import load_settings, positive_int
from ..failure import reported
from .score import score
from .sheet import write_sheet
from .stability import stability


def _sheet(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    print(f"{len(write_sheet(a.device))} decisions")


def _score(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    write_sheet(a.device)
    print(json.dumps(score(a.device), indent=1))


def _stability(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    settings = load_settings(ap, a)
    doc = stability(a.device, spawn(a, settings, DRY_RUN), load_prompts(ap, a, settings), a.sample, a.asks)
    print(f"{doc['stable']} of {doc['sample']} units stable over {doc['asks']} asks")


COMMANDS = {"sheet": _sheet, "score": _score, "stability": _stability}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.review", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    for name in sorted(COMMANDS):
        sub.add_parser(name).add_argument("device", type=Path, help="the device folder")
    p = sub.choices["stability"]
    p.add_argument("--sample", type=positive_int, default=20, help="units drawn across the apps")
    p.add_argument("--asks", type=positive_int, default=3, help="times each unit is asked")
    add_agent_args(p, role=ROLE)
    add_prompt_args(p)
    a = ap.parse_args(argv)
    return reported(lambda: COMMANDS[a.command](ap, a))


if __name__ == "__main__":
    sys.exit(main())
