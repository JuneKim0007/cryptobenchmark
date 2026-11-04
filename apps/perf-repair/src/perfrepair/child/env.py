"""The environment every child process gets: this process's, less the model secrets no child may bill or leak."""
from __future__ import annotations

import os

# the claude CLI bills an API key it finds before the logged-in subscription; the benchmark child needs none
WITHHELD_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def child_env(**extra: str) -> dict[str, str]:
    return {**{k: v for k, v in os.environ.items() if k not in WITHHELD_ENV}, **extra}
