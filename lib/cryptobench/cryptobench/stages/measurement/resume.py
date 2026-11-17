"""A rerun of a stopped run keeps the blocks it finished when its identity is the same; any other rerun starts fresh."""
import itertools, pathlib

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.results import identity
from cryptobench.shared.settings import effective_view
from cryptobench.stages.measurement.session import blocks, variant_order
from cryptobench.pipeline.warn import warn


def run_identity(effective, capture, suppress_errors):
    order = variant_order.chosen(effective_view.order_seed(read_yaml(effective)))[1]
    return identity.of(effective, capture, order, suppress_errors)


def kept(effective, capture, target, suppress_errors):
    """The paths under target a publish leaves in place: per pass the leading blocks whose records verify, their run folders and records, and
    preparation/ beside them."""
    if paths.finished(target):
        return ()
    found = records(target)
    if not found:
        return ()
    now = run_identity(effective, capture, suppress_errors)
    earlier = next((record["identity"] for _, _, record in found if isinstance(record, dict) and isinstance(record.get("identity"), dict)), None)
    changed = identity.changed(earlier, now) if earlier is not None else ["schema"]
    if changed:
        warn(f"identity_changed: {', '.join(changed)}; starting fresh")
        return ()
    keep, order = [], list(now["run"].get("passes") or {})
    for folder in sorted(dict.fromkeys(folder for folder, _, _ in found), key=lambda folder: order.index(folder.name) if folder.name in order else -1):
        keep += leading(target, folder, [(path, record) for at, path, record in found if at == folder], now)
    # the plan the kept runs were converted with; a newly measured process pulls its own over it
    plan = paths.RunTree(target).preparation.root
    return tuple(keep + ([relative(target, plan)] if keep and plan.is_dir() else []))


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


def leading(target, folder, found, now):
    """The kept paths of one pass: blocks 1..m in order, each verified; every record after the first that fails is not kept."""
    by_block = {block_of(path): (path, record) for path, record in found}
    kept, last = [], None
    for block in itertools.count(1):
        if block not in by_block:
            break
        path, record = by_block[block]
        reason = unverified(record, folder, block, now)
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


def block_of(path):
    return int(path.stem.rpartition("-")[2]) if path.stem.rpartition("-")[2].isdigit() else 0


def relative(target, path):
    return pathlib.PurePosixPath(path.relative_to(target).as_posix())


def unverified(record, folder, block, now):
    """Why a record cannot be kept, or None."""
    if isinstance(record, str):
        return record
    try:
        if record.get("schemaVersion") != blocks.SCHEMA:
            return f"schemaVersion {record.get('schemaVersion')}"
        if record["identity"] != now:
            return "identity differs from this run's"
        if record["outcome"] != blocks.FINISHED:
            return f"outcome {record['outcome']}"
        span = blocks.ranges(record["repetitions"], record["size"])
        if block > len(span) or (record["block"], record["runs"]["first"], record["runs"]["last"]) != span[block - 1]:
            return "its runs are not the block's"
        if [run["repetition"] for run in record["processes"]] != list(range(record["runs"]["first"], record["runs"]["last"] + 1)):
            return "its processes are not the block's runs"
        for run in record["processes"]:
            if blocks.run_files(folder / run["folder"], folder) != run["files"]:
                return f"{run['folder']}: its files differ from the record"
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
