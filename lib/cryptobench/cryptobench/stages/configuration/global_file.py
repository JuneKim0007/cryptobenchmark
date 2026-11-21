"""The global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, then the repository's."""
import os
import pathlib

from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared import paths
from cryptobench.shared.settings import authored


def global_config(argument):
    for named, where in ((argument, "--config"), (os.environ.get("CRYPTOBENCH_CONFIG"), "CRYPTOBENCH_CONFIG")):
        if named:
            if not pathlib.Path(named).is_file():
                raise CommandError(f"missing_file: {named} ({where})")
            return single(pathlib.Path(named).resolve())
    for candidate in (paths.user_global(), paths.repo().default_global):
        if candidate.is_file():
            return single(candidate.resolve())
    repository = paths.repo()
    raise CommandError(f"no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep {repository.default_global.relative_to(repository.root)}")


def single(path):
    """authored.read, which every Python reader of the authored file calls, merges no layers, so a composition is refused."""
    if "layers" in authored.read(path).document:
        raise CommandError(f"not_supported: {path} lists layers; the pipeline reads a single global.yaml")
    return path
