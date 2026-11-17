"""The digest of the code from a harness.yaml to a checked harness: perf-repair reads it from --identify, and a change reruns its apps."""
from cryptobench.shared import paths
from cryptobench.shared.digest.tree import digest_of
from cryptobench.shared.errors.coded import Coded

CODE = ("lib/cryptobench/cryptobench/stages/verification/scope/*.py", "apps/benchmark-runner/scope_generate.py", "apps/benchmark/modules/android/src/androidTest/**/Scope*.kt")


class CodeDigestError(Coded):
    pass


def digest(root=None, patterns=CODE):
    """A pattern that matches nothing is refused (digest_of), so no app misses a rerun after a move."""
    return digest_of(paths.code_root() if root is None else root, patterns, CodeDigestError)
