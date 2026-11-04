"""The global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, then the repository's."""
import os
import pathlib

from failure import fail
from repo import ROOT


def global_config(argument):
    if argument:
        if not pathlib.Path(argument).is_file():
            fail(f"missing_file: {argument} (--config)")
        return pathlib.Path(argument).resolve()
    for candidate in (os.environ.get("CRYPTOBENCH_CONFIG"),
                      pathlib.Path.home() / ".config/cryptobench/global.yaml", ROOT / "config/global.yaml"):
        if candidate and pathlib.Path(candidate).is_file():
            return pathlib.Path(candidate).resolve()
    fail("no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep config/global.yaml")
