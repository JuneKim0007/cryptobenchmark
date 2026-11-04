"""The digest of the code from a harness.yaml to a measured harness: perf-repair reads it from --identify, and a change reruns its apps."""
import hashlib

from repo import ROOT

CODE = ("scripts/scope/*.py", "scripts/scope_generate.py", "modules/android/src/androidTest/**/Scope*.kt")


class CodeDigestError(Exception):
    pass


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(root=ROOT, patterns=CODE):
    """A pattern that matches nothing is an error: after a move the digest would stop seeing those files, and no app would rerun."""
    lines = []
    for pattern in patterns:
        files = sorted(root.glob(pattern))
        if not files:
            raise CodeDigestError(f"missing_file: {pattern} matches nothing under {root}")
        lines += [f"{path.relative_to(root).as_posix()} {_sha256(path.read_bytes())}" for path in files]
    return _sha256("\n".join(lines).encode())
