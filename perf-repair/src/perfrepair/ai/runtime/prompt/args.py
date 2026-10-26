"""--prompts DIR for every command that calls a model, and the one library load per invocation."""
from __future__ import annotations

import argparse
from pathlib import Path

from .library import PromptError, PromptLibrary


def add_prompt_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompts", type=Path, metavar="DIR",
                        help="replace packaged prompts with the files in DIR, matched by their path relative to DIR "
                             "(e.g. DIR/review/grouping-review.system.md); a file matching no prompt is an error")


def load_prompts(parser: argparse.ArgumentParser, args: argparse.Namespace) -> PromptLibrary:
    try:
        return PromptLibrary.load(args.prompts)
    except PromptError as e:
        parser.error(str(e))
