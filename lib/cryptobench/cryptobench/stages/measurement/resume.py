"""A rerun of a stopped run keeps the blocks it finished when its identity is the same, checks the content of every kept run and launches its
failing cases again (RedoPlan); any other rerun starts fresh."""
import dataclasses, itertools, pathlib

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.results import run_record
from cryptobench.shared.settings.effective_view import RunView
from cryptobench.stages.measurement.session import blocks, variant_order
from cryptobench.stages.measurement.validation import expectation, rules
from cryptobench.shared.log.warn import warn

# a run whose energy capture spans the process is measured again whole, never by case
ENERGY_FILES = (paths.ENERGY_JSON, paths.ENERGY_DRY, paths.ENERGY_SAMPLES)


@dataclasses.dataclass(frozen=True)
class RedoPlan:
    """kept: the paths a publish leaves in place; cases: (pass, repetition) -> {case: [Finding]}, the failing cases of a kept run, launched
    again in it; findings: run -> [Finding], every kept run's content check."""
    kept: tuple = ()
    cases: dict = dataclasses.field(default_factory=dict)
    findings: dict = dataclasses.field(default_factory=dict)

    def of_pass(self, label):
        return {repetition: failed for (name, repetition), failed in self.cases.items() if name == label}


NOTHING = RedoPlan()


def record(effective, capture, options):
    """The run's record (shared/results/run_record.py) with the order its seed chooses."""
    order = variant_order.chosen(RunView(read_yaml(effective)).order_seed)[1]
    return run_record.of(effective, capture, order, options)


def planned(effective, capture, target, options):
    """At the publish of a measuring run: per pass the leading blocks whose records verify and whose runs pass check_run or fail only by
    case, their run folders, records and preparation/ beside them; printed before anything runs."""
    if paths.finished(target):
        return NOTHING
    found = records(target)
    if not found:
        return NOTHING
    now = record(effective, capture, options)
    earlier = next((record["identity"] for _, _, record in found if isinstance(record, dict) and isinstance(record.get("identity"), dict)), None)
    changed = run_record.changed(earlier, now) if earlier is not None else ["schema"]
    if changed:
        warn(f"identity_changed: {', '.join(changed)}; starting fresh")
        return NOTHING
    keep, cases, findings, order = [], {}, {}, list(now["run"].get("passes") or {})
    for folder in sorted(dict.fromkeys(folder for folder, _, _ in found), key=lambda folder: order.index(folder.name) if folder.name in order else -1):
        keep += leading(target, folder, [(path, record) for at, path, record in found if at == folder], now, cases, findings)
    # the plan the kept runs were converted with; a newly measured process pulls its own over it
    plan = paths.RunTree(target).preparation.root
    redo = RedoPlan(tuple(keep + ([relative(target, plan)] if keep and plan.is_dir() else [])), cases, findings)
    for (label, repetition), failed in cases.items():
        print(f"redo:      {label + ' pass: ' if label else ''}run {repetition}: "
              + ", ".join(f"{case} ({found[0].code})" for case, found in failed.items()))
    return redo


def records(target):
    """(pass folder, record path, record or the reason it could not be read) for every record under benchmark/."""
    benchmark = paths.RunTree(target).benchmark.root
    found = []
    for folder in sorted({path.parent.parent for path in benchmark.rglob(paths.BLOCK_PATTERN) if path.parent.name == paths.BLOCKS}):
        for path in paths.Measurement(folder).block_records():
            try:
                found.append((folder, path, read_yaml(path)))
            except Exception as error:
                found.append((folder, path, f"unreadable: {type(error).__name__}"))
    return found


def leading(target, folder, found, now, cases, findings):
    """The kept paths of one pass: blocks 1..m in order, each verified and its runs checked; every block after the first that fails is not
    kept. A kept run's failing cases join cases, its check findings."""
    by_block = {block_of(path): (path, record) for path, record in found}
    kept, last = [], None
    for block in itertools.count(1):
        if block not in by_block:
            break
        path, record = by_block[block]
        reason = unverified(record, block, now) or content(target, folder, record, cases, findings)
        if reason:
            warn(f"block_unverified: {path}: {reason}; it and every later block of this pass are measured again")
            break
        last = record
        for run in record["processes"]:
            kept.append(relative(target, folder / run["folder"]))
        kept.append(relative(target, path))
    if last:
        resumed(last)
    return kept


def content(target, folder, record, cases, findings):
    """check_run of every run of a verified record against its own run block; why the block cannot be kept, or None. A run failing only by
    case keeps the block with those cases to launch again; a fail of a whole-run file, or any fail in a run that captured energy, does not."""
    want = expectation.of(record["identity"]["run"], record["pass"])
    again = {}
    for run in record["processes"]:
        checked = rules.RunFolder(target, folder / run["folder"], folder, run["repetition"], tuple(run["problems"]), run["files"])
        found = rules.check_run(checked, want)
        findings[checked.run] = found
        failed = rules.failed(found)
        if failed and (any(finding.case is None for finding in failed) or any(name in ENERGY_FILES for name in run["files"])):
            return f"{run['folder']}: {failed[0].code}: {failed[0].detail}"
        if failed:
            again[(record["pass"], run["repetition"])] = {case: [f for f in failed if f.case == case] for case in rules.redone(failed)}
    cases.update(again)
    return None


def block_of(path):
    return int(path.stem.rpartition("-")[2]) if path.stem.rpartition("-")[2].isdigit() else 0


def relative(target, path):
    return pathlib.PurePosixPath(path.relative_to(target).as_posix())


def unverified(record, block, now):
    """Why a record cannot be kept, or None."""
    if isinstance(record, str):
        return record
    try:
        if not blocks.RECORD_DOC.accepts(record.get("schemaVersion")):
            return f"schemaVersion {record.get('schemaVersion')}"
        changed = run_record.changed(record["identity"], now)
        if changed:
            return f"identity differs from this run's: {', '.join(changed)}"
        if record["outcome"] != blocks.FINISHED:
            return f"outcome {record['outcome']}"
        span = blocks.ranges(record["repetitions"], record["size"])
        if block > len(span) or (record["block"], record["runs"]["first"], record["runs"]["last"]) != span[block - 1]:
            return "its runs are not the block's"
        if [run["repetition"] for run in record["processes"]] != list(range(record["runs"]["first"], record["runs"]["last"] + 1)):
            return "its processes are not the block's runs"
        if any(not {"problems", "relaunched", "files"} <= set(run) for run in record["processes"]):
            return "a process entry lacks problems, relaunched or files"
    except (KeyError, TypeError, AttributeError) as error:
        return f"malformed: {type(error).__name__}: {error}"
    return None


def span(first, last):
    return f"{first}" if first == last else f"{first}-{last}"


def resumed(last):
    label, blocks_kept, runs, total = last["pass"], last["block"], last["runs"]["last"], last["repetitions"]
    then = f"restarting at run {runs + 1}" if runs < total else "every run of it measured"
    print(f"resumed:   {label + ' pass: ' if label else ''}kept block{'s' if blocks_kept > 1 else ''} {span(1, blocks_kept)} "
          f"(run{'s' if runs > 1 else ''} {span(1, runs)}), {then}")


def note(target):
    """The manifest's resumed: per pass the blocks a publish kept and the runIds that measured them; read before this run records any."""
    kept = {}
    for _, _, record in records(target):
        if isinstance(record, dict):
            kept.setdefault(record.get("pass"), []).append(record)
    return [{"pass": label, "blocks": span(min(r["block"] for r in done), max(r["block"] for r in done)),
             "runs": span(min(r["runs"]["first"] for r in done), max(r["runs"]["last"] for r in done)),
             "runIds": sorted({r.get("runId") for r in done}, key=str)} for label, done in kept.items()]
