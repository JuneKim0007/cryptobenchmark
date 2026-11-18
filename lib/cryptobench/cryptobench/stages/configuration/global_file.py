"""The global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, then the repository's."""
import os
import pathlib

from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared import paths


def global_config(argument):
    for named, where in ((argument, "--config"), (os.environ.get("CRYPTOBENCH_CONFIG"), "CRYPTOBENCH_CONFIG")):
        if named:
            if not pathlib.Path(named).is_file():
                raise CommandError(f"missing_file: {named} ({where})")
            return single(pathlib.Path(named).resolve())
    for candidate in (paths.user_global(), paths.repo().default_global):
        if candidate.is_file():
            return single(candidate.resolve())
    raise CommandError("no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep config/global.yaml")


def single(path):
    """The run inputs digest, bundled providers, known vectors and dependency check read the authored file raw, so a composition is refused."""
    from cryptobench.shared.document.document import read_yaml  # dependencies.py imports this module before it checks yaml
    if "layers" in (read_yaml(path) or {}):
        raise CommandError(f"not_supported: {path} lists layers; the pipeline reads a single global.yaml")
    return path
