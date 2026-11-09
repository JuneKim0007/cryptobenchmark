"""The global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, then the repository's."""
import os
import pathlib

from failure import fail
from cryptobench import paths


def global_config(argument):
    for named, where in ((argument, "--config"), (os.environ.get("CRYPTOBENCH_CONFIG"), "CRYPTOBENCH_CONFIG")):
        if named:
            if not pathlib.Path(named).is_file():
                fail(f"missing_file: {named} ({where})")
            return pathlib.Path(named).resolve()
    for candidate in (paths.user_global(), paths.repo().default_global):
        if candidate.is_file():
            return candidate.resolve()
    fail("no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep config/global.yaml")
