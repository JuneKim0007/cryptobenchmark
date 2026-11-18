"""What makes two measuring runs the same run: the effective settings and selection without their stamps, the timed and the runner code, the
device build with its security patch and APEX versions, the case order and the suppressed androidx.benchmark errors."""
from cryptobench.shared import paths
from cryptobench.shared.device import capture as captured
from cryptobench.shared.digest.tree import digest_of
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results.run_inputs import digest

SCHEMA = 3
# a new probe restamps runId and generatedFrom; analysis only shows results
UNSTAMPED = ("runId", "generatedFrom", "analysis")
DETAILED = ("run", "code", "device")
ORIGIN = "from"


def timed_code(repo=None):
    """The source tree digest of what builds the measuring code; a pattern that matches nothing is refused (digest_of)."""
    repo = repo or paths.repo()
    return digest_of(repo.root, repo.timed_code, CommandError)


def code(repo=None):
    """timed: the measuring code's digest; runner: the digest of the host code around it."""
    repo = repo or paths.repo()
    return {"timed": timed_code(repo), "runner": digest_of(repo.root, repo.runner_code, CommandError)}


def of(effective, capture, order, suppress_errors):
    """run: the effective run block as written; selection: the digest of the rest; device: the capture's runtime block and the build facts;
    suppressErrors: --suppress-errors as a set."""
    document = read_yaml(effective)
    rest = {key: value for key, value in document.items() if key not in (*UNSTAMPED, "run")}
    if isinstance(rest.get("providers"), dict):
        rest["providers"] = without_origin(rest["providers"])
    return {"schema": SCHEMA, "run": document.get("run") or {}, "selection": digest(rest), "code": code(), "device": device(capture),
            "order": order, "suppressErrors": sorted({name.strip() for name in suppress_errors.split(",") if name.strip()})}


def without_origin(providers):
    """An entry's from: says which include picked it, not what is measured; reordering a suite's includes is the same run."""
    return {provider: {kind: {key: {field: value for field, value in entry.items() if field != ORIGIN} if isinstance(entry, dict) else entry
                              for key, entry in entries.items()} for kind, entries in types.items()} for provider, types in providers.items()}


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
