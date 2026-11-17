"""What makes two measuring runs the same run: the effective settings and selection without their stamps, the timed code, the device build
and the case order."""
from cryptobench.shared import paths
from cryptobench.shared.device import capture as captured
from cryptobench.shared.digest.tree import globbed, tree_digest
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results.run_inputs import digest

SCHEMA = 1
# a new probe restamps runId and generatedFrom; analysis only shows results
UNSTAMPED = ("runId", "generatedFrom", "analysis")
DETAILED = ("run", "device")


def timed_code(repo=None):
    """The source tree digest of what builds the measuring code; a pattern that matches nothing is refused, as code_digest refuses it."""
    repo = repo or paths.repo()
    files, empty = globbed(repo.gradle_root, repo.timed_code)
    if empty:
        raise CommandError(f"missing_file: {empty[0]} matches nothing under {repo.gradle_root}")
    return tree_digest(repo.gradle_root, files)


def of(effective, capture, order):
    """run: the effective run block as written; selection: the digest of the rest; device: the capture's runtime block."""
    document = read_yaml(effective)
    rest = {key: value for key, value in document.items() if key not in (*UNSTAMPED, "run")}
    return {"schema": SCHEMA, "run": document.get("run") or {}, "selection": digest(rest), "code": timed_code(),
            "device": captured.read_runtime(capture), "order": order}


def changed(before, after):
    """The fields that differ, a run or device key by its dotted name."""
    names = []
    for field in sorted(set(before) | set(after)):
        old, new = before.get(field), after.get(field)
        if old == new:
            continue
        if field in DETAILED and isinstance(old, dict) and isinstance(new, dict):
            names += [f"{field}.{key}" for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]
        else:
            names.append(field)
    return names
