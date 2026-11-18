"""A measuring run's record: its identity and the checkout that ran it; every block record and the manifest's run: hold it."""
import subprocess

from cryptobench.shared import paths
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import identity

PROVENANCE = ("commit", "clean")


def checkout(root=None):
    """commit: HEAD of the checkout; clean: no tracked or untracked change git reports. git that cannot say is missing_field."""
    root = root or paths.repo().root
    def git(*arguments):
        return subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    try:
        return {"commit": git("rev-parse", "HEAD"), "clean": git("status", "--porcelain") == ""}
    except (OSError, subprocess.SubprocessError) as error:
        raise CommandError(f"missing_field: commit, git cannot say for {root}: {type(error).__name__}") from error


def of(effective, capture, order, suppress_errors):
    return identity.of(effective, capture, order, suppress_errors) | checkout()


def changed(before, after):
    """identity.changed without the checkout: commit and clean say which tree ran, the code digests what it ran."""
    return [name for name in identity.changed(before, after) if name not in PROVENANCE]
