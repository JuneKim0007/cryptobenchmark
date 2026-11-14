"""The digest of the code from a harness.yaml to a checked harness: perf-repair reads it from --identify, and a change reruns its apps."""
from cryptobench.shared import paths
from cryptobench.shared.digest.tree import tree_digest
from cryptobench.shared.errors.coded import Coded

CODE = ("apps/benchmark-runner/scope/*.py", "apps/benchmark-runner/scope_generate.py", "apps/benchmark/modules/android/src/androidTest/**/Scope*.kt")


class CodeDigestError(Coded):
    pass


def digest(root=None, patterns=CODE):
    """A pattern that matches nothing is an error: after a move the digest would stop seeing those files, and no app would rerun."""
    root = paths.code_root() if root is None else root
    files = []
    for pattern in patterns:
        matched = sorted(root.glob(pattern))
        if not matched:
            raise CodeDigestError(f"missing_file: {pattern} matches nothing under {root}")
        files += matched
    return tree_digest(root, files)
