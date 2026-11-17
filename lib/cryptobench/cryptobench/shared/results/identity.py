"""What makes two measuring runs the same run: the effective settings and selection without their stamps, the timed code, the device build
with its security patch and APEX versions, the case order and the suppressed androidx.benchmark errors."""
from cryptobench.shared import paths
from cryptobench.shared.device import capture as captured
from cryptobench.shared.digest.tree import digest_of
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results.run_inputs import digest

SCHEMA = 2
# a new probe restamps runId and generatedFrom; analysis only shows results
UNSTAMPED = ("runId", "generatedFrom", "analysis")
DETAILED = ("run", "device")


def timed_code(repo=None):
    """The source tree digest of what builds the measuring code; a pattern that matches nothing is refused (digest_of)."""
    repo = repo or paths.repo()
    return digest_of(repo.gradle_root, repo.timed_code, CommandError)


def of(effective, capture, order, suppress_errors):
    """run: the effective run block as written; selection: the digest of the rest; device: the capture's runtime block and the build facts;
    suppressErrors: --suppress-errors as a set."""
    document = read_yaml(effective)
    rest = {key: value for key, value in document.items() if key not in (*UNSTAMPED, "run")}
    return {"schema": SCHEMA, "run": document.get("run") or {}, "selection": digest(rest), "code": timed_code(), "device": device(capture),
            "order": order, "suppressErrors": sorted({name.strip() for name in suppress_errors.split(",") if name.strip()})}


def device(capture):
    """facts.yaml beside the capture holds the build a device run read (stages/discovery/build_versions.py); a host run has none."""
    facts = paths.Discovery(capture.parent).facts
    build = read_yaml(facts).get("build") if facts.is_file() else None
    return captured.read_runtime(capture) | ({"build": build} if build is not None else {})


def changed(before, after, prefix=""):
    """The fields that differ, a run or device key by its dotted name, nested ones too."""
    names = []
    for field in sorted(set(before) | set(after)):
        old, new = before.get(field), after.get(field)
        if old == new:
            continue
        if (prefix or field in DETAILED) and isinstance(old, dict) and isinstance(new, dict):
            names += changed(old, new, f"{prefix}{field}.")
        else:
            names.append(prefix + field)
    return names
